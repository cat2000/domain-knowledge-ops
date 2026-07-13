#!/usr/bin/env python3
"""Dedicated S5 work-draft quality gate.

The gate validates the explicit Markdown contract of Agent-authored S5 drafts.
It does not decide business semantics and does not generate work-draft text.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_SCRIPTS = next(p for p in Path(__file__).resolve().parents if (p / "_install.py").is_file())
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
import _install

_install.bootstrap(__file__)

from distill._paths import DISTILLED_BY_ROOT, PASS_MARKER, REPO_ROOT

# Legacy zh-CN heading constants (kept for backward-compat error messages).
CLOSED_HEADING = "## 已闭环决策链"
UNRESOLVED_HEADING = "## 待裁决关键问题"
ORDER_PLAN_HEADING = "## 组织顺序说明"
OPTIONAL_STRUCTURED_DETAIL = "## 结构化明细转交"

# Token keys for required S5 sections (resolved to all-locale heading lists at runtime).
_S5_REQUIRED_SECTION_KEYS = (
    "s5_headings.overview_scope",
    "s5_headings.input_disposition",
    "s5_headings.domain_model",
    "s5_headings.ordering_rationale",
    "s5_headings.closed_chains",
    "s5_headings.pending_adjudication",
    "s5_headings.provenance",
)

# Token keys for closed-chain required fields (zh-CN + en).
_CHAIN_REQUIRED_FIELD_KEYS = (
    "s5_labels.domain_object",
    "s5_labels.state_change",
    "s5_labels.business_action",
    "s5_labels.display_field_anchor",
    "s5_labels.applicable_objects",
    "s5_labels.trigger_condition",
    "s5_labels.branch_or_action",
    "s5_labels.user_visible_effect",
    "s5_labels.evidence_source",
)

# Token keys for unresolved-issue required fields.
_UNRESOLVED_REQUIRED_FIELD_KEYS = (
    "s5_labels.pending_decision_point",
    "s5_labels.current_evidence",
    "s5_labels.pending_items",
    "s7_open_item_labels.suggested_owner",
    "s5_labels.decision_impact",
)

# Kept as fallback / for backward-compat usage in error messages.
REQUIRED_SECTIONS = (
    "## 概述与范围",
    "## 输入处置摘要",
    "## 领域模型",
    "## 组织顺序说明",
    "## 已闭环决策链",
    "## 待裁决关键问题",
    "## 溯源",
)
CHAIN_REQUIRED_FIELDS = (
    "领域对象",
    "状态变化",
    "业务动作",
    "展示容器/字段锚点",
    "适用对象",
    "触发条件",
    "分支或动作",
    "用户可见影响",
    "证据来源",
)
UNRESOLVED_REQUIRED_FIELDS = (
    "待裁决点",
    "当前证据",
    "待确认事项",
    "建议确认人",
    "决策影响",
)

CHAIN_TITLE_RE = re.compile(r"^###\s*链\s*(\d+)\s*[:：]\s*(.+?)\s*$", re.MULTILINE)
ORDER_PLAN_ITEM_RE = re.compile(r"链\s*(\d+)\s*[:：]\s*(.+?)(?:\s*—\s*|$)")
UNRESOLVED_TOKEN_RE = re.compile(r"(未确定|待确认|待定|unknown|tbd)", re.IGNORECASE)
UNRESOLVED_TITLE_RE = re.compile(r"^###\s*问题\s*(\d+)", re.MULTILINE)
UNRESOLVED_REF_RE = re.compile(r"关联待裁决\s*[:：]\s*问题\s*(\d+)")
UNRESOLVED_CHAIN_BINDING_RE = re.compile(r"关联链\s*[:：]([^\n。；;]*)")
SECTION_RE = re.compile(r"^##\s+", re.MULTILINE)
THIRD_LEVEL_RE = re.compile(r"^###\s+(.+)$", re.MULTILINE)


def check_work_draft_text(path: Path, text: str) -> list[str]:
    from runtime.deliverable_locale import all_locale_values as _all_locale

    rel = _rel(path)
    issues: list[str] = []

    # Check required sections — accept any locale's heading.
    for section_key in _S5_REQUIRED_SECTION_KEYS:
        variants = _all_locale(section_key)
        if not any(v in text for v in variants):
            display = variants[0] if variants else section_key
            issues.append(f"{rel}: missing section `{display}`")
    if issues:
        return issues

    # Extract sections using whichever locale's heading is present.
    input_disp = _section_any(text, *_all_locale("s5_headings.input_disposition"))
    closed = _section_any(text, *_all_locale("s5_headings.closed_chains"))
    unresolved = _section_any(text, *_all_locale("s5_headings.pending_adjudication"))
    order_plan = _section_any(text, *_all_locale("s5_headings.ordering_rationale"))

    issues.extend(_input_disposition_issues(rel, input_disp))
    chain_blocks = _blocks_by_heading(closed, CHAIN_TITLE_RE)
    issues.extend(_order_plan_issues(rel, order_plan, chain_blocks))
    issues.extend(_closed_chain_issues(rel, closed, chain_blocks))
    issues.extend(_unresolved_issue_issues(rel, unresolved))
    issues.extend(_reciprocal_link_issues(rel, chain_blocks, unresolved))

    struct_variants = _all_locale("s5_headings.structured_detail")
    active_struct = next((v for v in struct_variants if v in text), None)
    if active_struct:
        issues.extend(_structured_detail_issues(rel, _section(text, active_struct)))
    return issues


def collect_issues(root_id: str | None = None) -> list[str]:
    from runtime.deliverable_locale import work_draft_globs as _wdg

    roots = []
    if root_id:
        roots = [DISTILLED_BY_ROOT / str(root_id).strip()]
    elif DISTILLED_BY_ROOT.is_dir():
        roots = [p for p in sorted(DISTILLED_BY_ROOT.iterdir()) if p.is_dir()]
    else:
        return [f"missing curated tree: {DISTILLED_BY_ROOT}"]

    issues: list[str] = []
    for root in roots:
        if not root.is_dir():
            issues.append(f"missing curated root: {root}")
            continue
        seen: set[Path] = set()
        for glob_pat in _wdg():
            for path in sorted(root.glob(f"_deliver/*/{glob_pat}")):
                if path in seen:
                    continue
                seen.add(path)
                text = path.read_text(encoding="utf-8", errors="replace")
                if PASS_MARKER in text[:8000]:
                    continue
                issues.extend(check_work_draft_text(path, text))
    return issues


def _input_disposition_issues(rel: Path | str, text: str) -> list[str]:
    issues: list[str] = []
    for token in ("contract_candidate", "evidence_note", "noise_context"):
        if token not in text:
            issues.append(f"{rel}: input disposition section missing `{token}` handling")
    if not re.search(r"(语义归一|semantic\s+normalization|合并|降层|demot)", text, re.IGNORECASE):
        issues.append(f"{rel}: input disposition missing semantic normalization handling")
    if not re.search(r"(顺序归一|来源/顺序|source\s+order|business\s+decision\s+order|重排)", text, re.IGNORECASE):
        issues.append(f"{rel}: input disposition missing source/order normalization handling")
    return issues


def _order_plan_issues(rel: Path | str, order_plan: str, chains: list[tuple[int, str, str]]) -> list[str]:
    if not chains:
        return []
    planned = [
        (int(match.group(1)), _norm_title(match.group(2)))
        for match in ORDER_PLAN_ITEM_RE.finditer(order_plan)
    ]
    actual = [(idx, _norm_title(title)) for idx, title, _ in chains]
    if planned != actual:
        return [f"{rel}: order plan entries do not match closed chain ids/titles"]
    return []


def _closed_chain_issues(
    rel: Path | str,
    closed: str,
    chains: list[tuple[int, str, str]],
) -> list[str]:
    from runtime.deliverable_locale import all_locale_values as _all_locale

    issues: list[str] = []
    no_chain_phrases = _all_locale("phrases.no_closed_chain") or ["当前未形成已闭环决策链"]
    if not chains and not any(p in closed for p in no_chain_phrases):
        issues.append(f"{rel}: closed section has no `### 链 N` entries")
    if UNRESOLVED_TOKEN_RE.search(closed):
        issues.append(f"{rel}: unresolved tokens appear inside closed section; move them to `{UNRESOLVED_HEADING}`")
    for idx, _title, block in chains:
        missing = [
            _all_locale(key)[0] if _all_locale(key) else key.split(".")[-1]
            for key in _CHAIN_REQUIRED_FIELD_KEYS
            if not any(_has_field(block, v) for v in _all_locale(key))
        ]
        if missing:
            issues.append(f"{rel}: closed chain {idx} missing required fields: {', '.join(missing)}")
    return issues


def _unresolved_issue_issues(rel: Path | str, unresolved: str) -> list[str]:
    from runtime.deliverable_locale import all_locale_values as _all_locale

    issues: list[str] = []
    # Binding check: accept zh (关联链/关联前置域) and en (Associated chain/Associated upstream).
    assoc_chain = _all_locale("s5_labels.associated_chain")
    assoc_upstream = _all_locale("s5_labels.associated_upstream")
    binding_re = re.compile(
        r"(?:关联(?:链|前置域)|"
        + "|".join(re.escape(v) for v in assoc_chain + assoc_upstream if v)
        + r")\s*[:：]",
    )
    for issue_id, block in _unresolved_blocks(unresolved).items():
        if not binding_re.search(block):
            issues.append(f"{rel}: unresolved issue {issue_id} lacks `关联链` or `关联前置域` binding")
        missing = [
            _all_locale(key)[0] if _all_locale(key) else key.split(".")[-1]
            for key in _UNRESOLVED_REQUIRED_FIELD_KEYS
            if not any(_has_field(block, v) for v in _all_locale(key))
        ]
        if missing:
            issues.append(f"{rel}: unresolved issue {issue_id} missing required fields: {', '.join(missing)}")
    return issues


def _reciprocal_link_issues(
    rel: Path | str,
    chains: list[tuple[int, str, str]],
    unresolved: str,
) -> list[str]:
    issues: list[str] = []
    unresolved_by_id = _unresolved_blocks(unresolved)
    for chain_idx, _title, block in chains:
        for ref in UNRESOLVED_REF_RE.finditer(block):
            issue_id = int(ref.group(1))
            issue_block = unresolved_by_id.get(issue_id)
            if issue_block is None:
                issues.append(f"{rel}: chain {chain_idx} references missing unresolved issue {issue_id}")
                continue
            binding = UNRESOLVED_CHAIN_BINDING_RE.search(issue_block)
            if not binding:
                issues.append(f"{rel}: unresolved issue {issue_id} referenced by chain {chain_idx} lacks reciprocal `关联链` binding")
                continue
            bound = {int(x) for x in re.findall(r"链\s*(\d+)", binding.group(1))}
            if chain_idx not in bound:
                issues.append(
                    f"{rel}: chain {chain_idx} references issue {issue_id}, but the issue binds chains {sorted(bound) or 'none'}"
                )
    return issues


def _structured_detail_issues(rel: Path | str, text: str) -> list[str]:
    blocks = _third_level_blocks(text)
    if not blocks:
        return [f"{rel}: `{OPTIONAL_STRUCTURED_DETAIL}` must use `###` headings"]
    issues: list[str] = []
    for title, block in blocks:
        if not _has_queryable_table(block) and not _has_layered_list(block):
            issues.append(f"{rel}: structured detail `{title}` must use a table or layered list")
    return issues


def _section(text: str, heading: str) -> str:
    pattern = re.compile(rf"^{re.escape(heading)}\s*$", re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return ""
    rest = text[match.end() :]
    next_match = SECTION_RE.search(rest)
    return rest[: next_match.start()] if next_match else rest


def _section_any(text: str, *headings: str) -> str:
    """Return the section body for the first heading found in text."""
    for heading in headings:
        result = _section(text, heading)
        if result:
            return result
    return ""


def _blocks_by_heading(text: str, pattern: re.Pattern[str]) -> list[tuple[int, str, str]]:
    matches = list(pattern.finditer(text))
    blocks: list[tuple[int, str, str]] = []
    for idx, match in enumerate(matches):
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        blocks.append((int(match.group(1)), match.group(2).strip(), text[start:end]))
    return blocks


def _unresolved_blocks(text: str) -> dict[int, str]:
    matches = list(UNRESOLVED_TITLE_RE.finditer(text))
    blocks: dict[int, str] = {}
    for idx, match in enumerate(matches):
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        blocks[int(match.group(1))] = text[start:end]
    return blocks


def _third_level_blocks(text: str) -> list[tuple[str, str]]:
    matches = list(THIRD_LEVEL_RE.finditer(text))
    blocks: list[tuple[str, str]] = []
    for idx, match in enumerate(matches):
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        blocks.append((match.group(1).strip(), text[start:end]))
    return blocks


def _has_field(block: str, field: str) -> bool:
    return bool(re.search(rf"^\s*[-*]\s*{re.escape(field)}\s*[:：]\s*\S", block, re.MULTILINE))


def _has_queryable_table(block: str) -> bool:
    lines = [line.strip() for line in block.splitlines()]
    for idx, line in enumerate(lines[:-1]):
        if line.startswith("|") and line.endswith("|") and re.match(r"^\|[\s:|-]+\|$", lines[idx + 1]):
            return True
    return False


def _has_layered_list(block: str) -> bool:
    lines = block.splitlines()
    for idx, line in enumerate(lines[:-1]):
        if re.match(r"^-\s+\S", line) and re.search(r"^\s{2,}-\s+\S", "\n".join(lines[idx + 1 :]), re.MULTILINE):
            return True
    return False


def _norm_title(text: str) -> str:
    return re.sub(r"\s+", "", text.strip().lower())


def _rel(path: Path) -> Path | str:
    try:
        return path.relative_to(REPO_ROOT)
    except ValueError:
        return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Check S5 work draft Markdown contract.")
    parser.add_argument("--root-id", help="Only check this curated root ID.")
    parser.add_argument("--warn-only", action="store_true", help="Print issues but exit 0.")
    args = parser.parse_args()

    issues = collect_issues(args.root_id)
    if issues:
        print("S5 work draft quality issues:", file=sys.stderr)
        for issue in issues:
            print(f"  {issue}", file=sys.stderr)
    print(f"S5 work draft quality: issues={len(issues)}")
    return 0 if not issues or args.warn_only else 1


if __name__ == "__main__":
    raise SystemExit(main())
