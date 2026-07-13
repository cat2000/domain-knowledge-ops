#!/usr/bin/env python3
"""
Heuristic checks on curated Markdown (no LLM).

Goals:
  - Catch common anti-patterns from generate-knowledge-from-wiki RUNBOOK S4–S6 / distill-quality-bar.md:
      * Many "### [Title](https://...atlassian...)" headings → likely Confluence mirror skeleton
      * Links back to domain-knowledge/materialized/ in body → forbidden for reader-facing distill
  - Skip deep checks for Pass stubs (## 非业务判定（Cursor） near top).

Does NOT judge semantic correctness of business rules.

Exit code: 0 if no violations (or --warn-only), else 1.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_SCRIPTS = next(p for p in Path(__file__).resolve().parents if (p / "_install.py").is_file())
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
import _install

_install.bootstrap(__file__)

from distill._paths import DISTILLED_BY_ROOT, PASS_MARKER, REPO_ROOT
from distill.structured_source import structured_source_signal
CONFLUENCE_MIRROR_HEADING = re.compile(
    r"^###\s+\[[^\]]+\]\(\s*https?://[^\)]*atlassian[^\)]*\)",
    re.IGNORECASE,
)
RULES_MD_LINK = re.compile(r"[\[\(]?\s*domain-knowledge/materialized/", re.IGNORECASE)
S4_CLOSED_HEADING = "## 已闭环决策链"
S4_UNRESOLVED_HEADING = "## 待裁决关键问题"
S5_STRUCTURED_DETAIL_HEADING = "## 结构化明细转交"
S4_INPUT_DISPOSITION_HEADING = "## 输入处置摘要"
S4_DOMAIN_MODEL_HEADING = "## 领域模型"
S4_ORDER_PLAN_HEADING = "## 组织顺序说明"


def _active_heading(text: str, token_key: str, fallback: str) -> str:
    """Return the first heading variant (any locale) found in text, or fallback."""
    try:
        from runtime.deliverable_locale import all_locale_values
        for h in all_locale_values(token_key):
            if h in text:
                return h
    except ImportError:
        pass
    return fallback if fallback in text else ""


def _any_heading_present(text: str, token_key: str, fallback: str) -> bool:
    """True if any locale variant of token_key is in text."""
    try:
        from runtime.deliverable_locale import all_locale_values
        candidates = all_locale_values(token_key)
        if candidates:
            return any(h in text for h in candidates)
    except ImportError:
        pass
    return fallback in text


def _is_work_draft(name: str) -> bool:
    """True for work-draft files in any deliverable locale."""
    try:
        from runtime.deliverable_locale import work_draft_globs
        return any(name.endswith(g.lstrip("*")) for g in work_draft_globs())
    except ImportError:
        return name.endswith("领域知识-工作稿.md")
S4_CHAIN_HEADING_RE = re.compile(r"^###\s*链\s*\d+", re.IGNORECASE)
S4_CHAIN_TITLE_RE = re.compile(r"^###\s*链\s*(\d+)\s*[:：]\s*(.+?)\s*$", re.IGNORECASE)
S4_ORDER_PLAN_ITEM_RE = re.compile(r"链\s*(\d+)\s*[:：]\s*(.+?)(?:\s*—\s*|$)", re.IGNORECASE)
S4_NO_CLOSED_CHAIN_RE = re.compile(r"(当前未形成已闭环决策链|无已闭环决策链|未发现可闭环业务规则)")
S4_PLACEHOLDER_RE = re.compile(r"(待补充|按来源条件触发|按来源分支动作执行|待确认对象|按来源动作触发)")
S4_UNRESOLVED_TOKEN_RE = re.compile(r"(未确定|待确认|待定|unknown|tbd)", re.IGNORECASE)
S4_UNRESOLVED_HEADING_RE = re.compile(r"^###\s*问题\s*\d+", re.IGNORECASE)
S4_UNRESOLVED_BINDING_RE = re.compile(r"关联(?:链|前置域)\s*[:：]")
S4_UNRESOLVED_IMPACT_RE = re.compile(r"决策影响\s*[:：]")
S4_UNRESOLVED_REF_RE = re.compile(r"关联待裁决\s*[:：]\s*问题\s*(\d+)")
S4_UNRESOLVED_ID_RE = re.compile(r"^###\s*问题\s*(\d+)", re.IGNORECASE)
S4_UNRESOLVED_CHAIN_BINDING_RE = re.compile(r"关联链\s*[:：]([^\n。；;]*)")
S4_DOMAIN_MODEL_REQUIRED_RE = re.compile(r"(一等业务对象|领域对象|指标/字段|对象关系|状态机|状态转换|展示容器|字段锚点)")
S4_CHAIN_MODEL_FIELD_RE = re.compile(r"(领域对象|状态变化|业务动作|展示容器\s*/\s*字段锚点|展示容器|字段锚点)\s*[:：]")
S4_CHAIN_OBJECT_LINE_RE = re.compile(r"^\s*[-*]\s*领域对象\s*[:：](.*)$", re.IGNORECASE | re.MULTILINE)
S4_MODEL_LINE_RE = re.compile(r"^\s*[-*]\s*(一等业务对象|指标/字段|展示容器)\s*[:：](.*)$", re.IGNORECASE | re.MULTILINE)
S4_MODEL_SECTION_RE = re.compile(
    r"^###\s*(一等业务对象|指标/字段|展示容器)\s*$",
    re.IGNORECASE | re.MULTILINE,
)
S4_MODEL_SECTION_ITEM_RE = re.compile(r"^\s*[-*]\s*(?:\*\*)?(.+?)(?:\*\*)?\s*(?:[:：].*)?$")
S4_DOMAIN_OBJECT_LINE_RE = re.compile(r"^\s*[-*]\s*(?:一等业务对象|领域对象)\s*[:：](.*)$", re.IGNORECASE)
S4_TYPED_MODEL_DIMENSIONS = ("一等业务对象", "指标/字段", "展示容器", "对象关系", "状态机/状态转换")
S4_DOMAIN_OBJECT_MIXED_LAYER_RE = re.compile(
    r"(字段|指标|公式|进度|金额|额度|目标差距|本周需|weekly-needed|progress|card|page|list|detail|API|接口|卡片|页面|列表|详情页)",
    re.IGNORECASE,
)
S4_DOMAIN_BOUNDARY_OBJECT_RE = re.compile(
    r"(排除|噪声|支撑材料|待归属|待迁移|工程协作|代码风格|发布/合规|发布协作|"
    r"support material|engineering style material|code style|release\s*/\s*compliance)",
    re.IGNORECASE,
)
S4_ORDER_ARROW_RE = re.compile(r"(->|→)")
S4_HALF_CLOSED_GAP_RE = re.compile(
    r"(S5 前需确认|需确认|未明确|缺口|支撑未闭环|"
    r"(API|字段|检测方式|实现)[^\n。；;]*(未明确|缺失|待裁决|需裁决))"
)
S4_LINKED_DECISION_RE = re.compile(r"关联待裁决\s*[:：]\s*问题\s*\d+")
S4_LEGACY_PROJECTION_RE = re.compile(
    r"(本稿由\s*S3\s*`?decision-atoms`?.*生成|当前模块共有\s*`?\d+`?\s*条\s*decision atoms)",
    re.IGNORECASE,
)
S4_HIGH_VALUE_EVIDENCE_DISPOSITION_RE = re.compile(
    r"(high-value\s+evidence|高价值\s*evidence|高价值证据|evidence\s*型业务规则|evidence.*提升)",
    re.IGNORECASE,
)
S4_NORMALIZATION_DISPOSITION_RE = re.compile(
    r"(语义归一|归一|合并|主规则|展示位置|字段锚点|跨\s*(UI|API|页面|容器)|重复|"
    r"semantic\s+normalization|demot(?:e|ed|ion)|merged?|duplicate|cross[-\s]*(UI|API|page|container))",
    re.IGNORECASE,
)
S4_ORDER_DISPOSITION_RE = re.compile(
    r"(顺序归一|业务顺序|执行顺序|判定顺序|来源顺序|同页顺序|重排|"
    r"source\s*/?\s*order\s+normalization|source\s+order|business\s+(decision\s+)?order|reorgan(?:ize|ized|ise|ised))",
    re.IGNORECASE,
)
S4_EVIDENCE_BUSINESS_ANCHOR_RE = re.compile(
    r"("
    r"=|>=|<=|>|<|true|false|visible|invisible|status|target|card|widget|field|"
    r"公式|计算|阈值|状态|枚举|展示|显示|卡片|可见|隐藏|时间窗|周|weeks?|"
    r"资格|奖励|金额|CVP|SVP|FPV|已读率|送达率|目标|进度|职称|title"
    r")",
    re.IGNORECASE,
)
S5_STRUCTURED_DETAIL_RE = re.compile(
    r"("
    r"=|>=|<=|>|<|true|false|status|case\s*\d+|field|target|"
    r"公式|计算|阈值|状态|枚举|展示|显示|字段|列表|映射|编号|档位|等级|职称|"
    r"时间窗|周|weeks?|日期|CVP|SVP|FPV|率|目标|进度|升级|条件"
    r")",
    re.IGNORECASE,
)
S5_STRUCTURED_DETAIL_ROLES = {
    "threshold_anchor",
    "time_window",
    "outcome_cue",
    "presentation_cue",
    "condition_or_rule_cue",
    "named_business_structure",
}
def main() -> int:
    parser = argparse.ArgumentParser(description="Heuristic quality checks for curated/.")
    parser.add_argument("--root-id", help="Only check this root page ID directory.")
    parser.add_argument(
        "--max-confluence-mirror-headings",
        type=int,
        default=3,
        help="Fail if a non-Pass file has this many ### [x](atlassian...) headings (default: 3).",
    )
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Print issues but exit 0.",
    )
    parser.add_argument(
        "--s4-min-propositions-per-source",
        type=int,
        default=2,
        help="For S4 work drafts, require coverage for source URLs with at least this many high-value propositions.",
    )
    parser.add_argument(
        "--s4-max-required-sources",
        type=int,
        default=8,
        help="Max required source URLs per S4 draft.",
    )
    parser.add_argument(
        "--s5-min-structured-detail-items",
        type=int,
        default=6,
        help="Require S5 structured detail handoff when S3 has at least this many structured detail candidates.",
    )
    args = parser.parse_args()

    if not DISTILLED_BY_ROOT.is_dir():
        print(f"Missing curated tree: {DISTILLED_BY_ROOT}", file=sys.stderr)
        return 0 if args.warn_only else 1

    violations: list[str] = []
    checked = 0
    skipped_pass = 0
    skipped_readme = 0

    for root_dir in sorted(DISTILLED_BY_ROOT.iterdir()):
        if not root_dir.is_dir():
            continue
        rid = root_dir.name
        if args.root_id and rid != args.root_id:
            continue
        for md in sorted(root_dir.rglob("*.md")):
            if md.name == "README.md":
                skipped_readme += 1
                continue
            if md.name.endswith("命题清单.md"):
                # S3.5 proposition worksheet is not a reader-facing distill artifact.
                skipped_readme += 1
                continue
            if md.name.endswith("decision-atoms.md") or md.name.endswith("conflict-ledger.md"):
                skipped_readme += 1
                continue
            text = md.read_text(encoding="utf-8", errors="replace")
            if is_pass_stub(text):
                skipped_pass += 1
                continue
            checked += 1
            rel = md.relative_to(REPO_ROOT)

            mirror_h = sum(1 for line in text.splitlines() if CONFLUENCE_MIRROR_HEADING.match(line.strip()))
            if mirror_h >= args.max_confluence_mirror_headings:
                violations.append(
                    f"{rel}: {mirror_h} Confluence-style '### [title](atlassian…)' headings "
                    f"(>= {args.max_confluence_mirror_headings}); likely page mirror — "
                    f"see domain-knowledge/distill-quality-bar.md"
                )

            # 允许在「## 溯源」及之后写 `domain-knowledge/materialized/…` 一行（初稿溯源）；禁止出现在正文主体
            body_only = text.split("\n## 溯源", 1)[0] if "\n## 溯源" in text else text
            if RULES_MD_LINK.search(body_only):
                violations.append(
                    f"{rel}: links or paths to domain-knowledge/materialized/ before '## 溯源' — "
                    f"put aggregation-draft paths only under ## 溯源 (see distill-quality-bar.md)"
                )
            if _is_work_draft(md.name):
                violations.extend(_s4_source_coverage_violations(md, text, args))
                violations.extend(_s4_evidence_disposition_violations(md, text))
                violations.extend(_s5_structured_detail_handoff_violations(md, text, args))
                violations.extend(_s4_structure_violations(md, text))

    if violations:
        print("curated quality issues:", file=sys.stderr)
        for v in violations:
            print(f"  {v}", file=sys.stderr)
    print(
        f"Quality check: checked_non_pass={checked} skipped_pass={skipped_pass} "
        f"readme_skipped={skipped_readme} issues={len(violations)}"
    )

    if violations and not args.warn_only:
        return 1
    return 0
def is_pass_stub(text: str) -> bool:
    head = text[:6000]
    return PASS_MARKER in head


def _s4_source_coverage_violations(md: Path, text: str, args: argparse.Namespace) -> list[str]:
    rel = md.relative_to(REPO_ROOT)
    slug = md.parent.name.strip()
    if not slug:
        return []
    root_dir = md.parents[2] if len(md.parents) >= 3 else None
    if root_dir is None:
        return []
    props_json = root_dir / "_aggregate" / slug / f"{slug}-propositions.json"
    if not props_json.is_file():
        return []
    try:
        payload = json.loads(props_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return [f"{rel}: cannot parse {props_json.relative_to(REPO_ROOT)} for S4 source coverage"]

    source_counts: dict[str, int] = {}
    for page in list(payload.get("pages") or []):
        page_url = str(dict(page).get("source_url") or "").strip()
        if not page_url:
            continue
        for item in list(dict(page).get("proposition_items") or []):
            d = dict(item)
            if not _is_high_value_s4_input(d):
                continue
            source_counts[page_url] = int(source_counts.get(page_url) or 0) + 1
    if not source_counts:
        return []

    candidates = [
        (url, cnt)
        for url, cnt in sorted(source_counts.items(), key=lambda kv: kv[1], reverse=True)
        if cnt >= int(args.s4_min_propositions_per_source or 2)
    ][: int(args.s4_max_required_sources or 8)]
    if not candidates:
        return []

    missing = [url for url, _ in candidates if url not in text]
    if not missing:
        return []
    sample = ", ".join(missing[:3])
    return [
        f"{rel}: missing key S3 source coverage in S4 draft ({len(missing)}/{len(candidates)} urls missing), e.g. {sample}"
    ]


def _s4_evidence_disposition_violations(md: Path, text: str) -> list[str]:
    rel = md.relative_to(REPO_ROOT)
    slug = md.parent.name.strip()
    if not slug:
        return []
    root_dir = md.parents[2] if len(md.parents) >= 3 else None
    if root_dir is None:
        return []
    props_json = root_dir / "_aggregate" / slug / f"{slug}-propositions.json"
    if not props_json.is_file():
        return []
    try:
        payload = json.loads(props_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return [f"{rel}: cannot parse {props_json.relative_to(REPO_ROOT)} for S4 evidence disposition"]

    high_value_sources: dict[str, int] = {}
    for page in list(payload.get("pages") or []):
        page_dict = dict(page)
        page_url = str(page_dict.get("source_url") or "").strip()
        if not page_url:
            continue
        for item in list(page_dict.get("proposition_items") or []):
            d = dict(item)
            if _is_high_value_evidence_candidate(d):
                high_value_sources[page_url] = int(high_value_sources.get(page_url) or 0) + 1

    if not high_value_sources:
        return []

    issues: list[str] = []
    _dm_h = _active_heading(text, "s5_headings.domain_model", S4_DOMAIN_MODEL_HEADING)
    _op_h = _active_heading(text, "s5_headings.ordering_rationale", S4_ORDER_PLAN_HEADING)
    _cl_h = _active_heading(text, "s5_headings.closed_chains", S4_CLOSED_HEADING)
    _id_h = _active_heading(text, "s5_headings.input_disposition", S4_INPUT_DISPOSITION_HEADING)
    _ur_h = _active_heading(text, "s5_headings.pending_adjudication", S4_UNRESOLVED_HEADING)
    disposition_end_heading = _dm_h or _op_h or _cl_h
    disposition_part = (
        text.split(_id_h, 1)[1].split(disposition_end_heading, 1)[0]
        if _id_h and disposition_end_heading and _id_h in text and disposition_end_heading in text
        else ""
    )
    if not S4_HIGH_VALUE_EVIDENCE_DISPOSITION_RE.search(disposition_part):
        issues.append(f"{rel}: input disposition missing explicit high-value evidence uplift/disposition")

    closed_part = text.split(_cl_h, 1)[1].split(_ur_h, 1)[0] if _cl_h and _ur_h and _cl_h in text and _ur_h in text else ""
    has_closed_chain = any(S4_CHAIN_HEADING_RE.match(ln.strip()) for ln in closed_part.splitlines())
    if not has_closed_chain:
        missing_sources = [url for url in sorted(high_value_sources) if url not in text]
        if missing_sources:
            sample = ", ".join(missing_sources[:3])
            issues.append(
                f"{rel}: no closed chain but high-value evidence sources are not explicitly disposed, e.g. {sample}"
            )
    return issues


def _is_high_value_s4_input(item: dict[str, object]) -> bool:
    candidate_type = str(item.get("candidate_type") or "").strip()
    if candidate_type == "noise_context":
        return False
    if candidate_type == "contract_candidate":
        return True
    track = str(item.get("decision_track") or "").strip()
    if track == "unresolved_critical":
        return True
    roles = {str(x).strip() for x in list(item.get("semantic_roles") or []) if str(x).strip()}
    if "noise_cue" in roles:
        return False
    score = int(item.get("causality_score") or 0)
    if score < 7:
        return False
    if roles & {"branch_marker", "unresolved_marker"}:
        return True
    if "condition_or_rule_cue" in roles and "outcome_cue" in roles:
        return True
    if "time_window" in roles and "outcome_cue" in roles:
        return True
    return False


def _is_high_value_evidence_candidate(item: dict[str, object]) -> bool:
    candidate_type = str(item.get("candidate_type") or "").strip()
    if candidate_type != "evidence_note":
        return False
    track = str(item.get("decision_track") or "").strip()
    if track == "noise_context":
        return False
    roles = {str(x).strip() for x in list(item.get("semantic_roles") or []) if str(x).strip()}
    if "noise_cue" in roles:
        return False
    if roles & {
        "threshold_anchor",
        "time_window",
        "outcome_cue",
        "presentation_cue",
        "condition_or_rule_cue",
        "named_business_structure",
    }:
        return True
    text = str(item.get("text") or "").strip()
    return bool(text and S4_EVIDENCE_BUSINESS_ANCHOR_RE.search(text))


def _s5_structured_detail_handoff_violations(md: Path, text: str, args: argparse.Namespace) -> list[str]:
    rel = md.relative_to(REPO_ROOT)
    slug = md.parent.name.strip()
    if not slug:
        return []
    root_dir = md.parents[2] if len(md.parents) >= 3 else None
    if root_dir is None:
        return []
    props_json = root_dir / "_aggregate" / slug / f"{slug}-propositions.json"
    if not props_json.is_file():
        return []
    try:
        payload = json.loads(props_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return [f"{rel}: cannot parse {props_json.relative_to(REPO_ROOT)} for S5 structured detail handoff"]

    detail_items: list[dict[str, object]] = []
    structured_pages: list[dict[str, object]] = []
    for page in list(payload.get("pages") or []):
        page_dict = dict(page)
        if _page_has_structured_source_signal(page_dict):
            structured_pages.append(page_dict)
        for item in list(page_dict.get("proposition_items") or []):
            d = dict(item)
            if _is_structured_detail_candidate(d):
                detail_items.append(d)

    threshold = int(args.s5_min_structured_detail_items or 6)
    requires_handoff = len(detail_items) >= threshold or bool(structured_pages)
    _sd_h = _active_heading(text, "s5_headings.structured_detail", S5_STRUCTURED_DETAIL_HEADING)
    if not requires_handoff:
        if _sd_h:
            return _structured_detail_section_violations(rel, text, _sd_h)
        return []

    issues: list[str] = []
    if not _sd_h:
        sample = "; ".join(str(item.get("text") or "").strip()[:60] for item in detail_items[:3])
        page_sample = ", ".join(str(page.get("title") or page.get("materialized_file") or "") for page in structured_pages[:3])
        reason = (
            f"{len(detail_items)} structured detail candidates"
            + (f" and {len(structured_pages)} structured source pages" if structured_pages else "")
        )
        issues.append(
            f"{rel}: missing `{S5_STRUCTURED_DETAIL_HEADING}` despite {reason}"
            + (f", source pages: {page_sample}" if page_sample else "")
            + (f", e.g. {sample}" if sample else "")
        )
        return issues
    issues.extend(_structured_detail_section_violations(rel, text, _sd_h))
    return issues


def _page_has_structured_source_signal(page: dict[str, object]) -> bool:
    structured = dict(page.get("structured_source") or {})
    if bool(structured.get("has_structured_source")):
        return True
    materialized_file = str(page.get("materialized_file") or "").strip()
    if not materialized_file:
        return False
    source_path = REPO_ROOT / materialized_file
    if not source_path.is_file():
        return False
    try:
        source_text = source_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return bool(structured_source_signal(source_text).get("has_structured_source"))


def _is_structured_detail_candidate(item: dict[str, object]) -> bool:
    candidate_type = str(item.get("candidate_type") or "").strip()
    if candidate_type == "noise_context":
        return False
    track = str(item.get("decision_track") or "").strip()
    if track == "noise_context":
        return False
    roles = {str(x).strip() for x in list(item.get("semantic_roles") or []) if str(x).strip()}
    if "noise_cue" in roles:
        return False
    text = str(item.get("text") or "").strip()
    if S4_DOMAIN_BOUNDARY_OBJECT_RE.search(text):
        return False
    decision_block = dict(item.get("decision_block") or {})
    decision_text = " ".join(str(value or "") for value in decision_block.values())
    if roles & S5_STRUCTURED_DETAIL_ROLES and S5_STRUCTURED_DETAIL_RE.search(f"{text} {decision_text}"):
        return True
    return candidate_type == "contract_candidate" and bool(S5_STRUCTURED_DETAIL_RE.search(f"{text} {decision_text}"))


def _structured_detail_section_violations(
    rel: Path, text: str, heading: str = S5_STRUCTURED_DETAIL_HEADING
) -> list[str]:
    detail = _section(text, heading)
    if not detail.strip():
        return [f"{rel}: `{heading}` is empty"]
    blocks = _third_level_blocks(detail)
    if not blocks:
        return [f"{rel}: `{heading}` must use `###` headings"]
    issues: list[str] = []
    for title, block in blocks:
        if not block.strip():
            issues.append(f"{rel}: structured detail `{title}` has no content")
            continue
        if not _has_queryable_table(block) and not _has_layered_list(block):
            issues.append(f"{rel}: structured detail `{title}` must use a table or layered list")
    return issues


def _section(text: str, heading: str) -> str:
    if heading not in text:
        return ""
    rest = text.split(heading, 1)[1]
    next_heading = re.search(r"\n##\s+", rest)
    return rest[: next_heading.start()] if next_heading else rest


def _third_level_blocks(text: str) -> list[tuple[str, str]]:
    blocks: list[tuple[str, str]] = []
    matches = list(re.finditer(r"^###\s+(.+)$", text, re.MULTILINE))
    for idx, match in enumerate(matches):
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        blocks.append((match.group(1).strip(), text[start:end]))
    return blocks


def _has_queryable_table(block: str) -> bool:
    lines = [line.strip() for line in block.splitlines()]
    for idx, line in enumerate(lines[:-1]):
        if not (line.startswith("|") and line.endswith("|")):
            continue
        if re.match(r"^\|[\s:|-]+\|$", lines[idx + 1]):
            return True
    return False


def _has_layered_list(block: str) -> bool:
    lines = block.splitlines()
    for idx, line in enumerate(lines[:-1]):
        if not re.match(r"^-\s+\S", line):
            continue
        following = "\n".join(lines[idx + 1 :])
        if re.search(r"^\s{2,}-\s+\S", following, re.MULTILINE):
            return True
    return False


def _s4_structure_violations(md: Path, text: str) -> list[str]:
    rel = md.relative_to(REPO_ROOT)
    issues: list[str] = []

    # Resolve active headings for each section (any locale).
    _id_h = _active_heading(text, "s5_headings.input_disposition", S4_INPUT_DISPOSITION_HEADING)
    _dm_h = _active_heading(text, "s5_headings.domain_model", S4_DOMAIN_MODEL_HEADING)
    _op_h = _active_heading(text, "s5_headings.ordering_rationale", S4_ORDER_PLAN_HEADING)
    _cl_h = _active_heading(text, "s5_headings.closed_chains", S4_CLOSED_HEADING)
    _ur_h = _active_heading(text, "s5_headings.pending_adjudication", S4_UNRESOLVED_HEADING)

    if S4_LEGACY_PROJECTION_RE.search(text):
        issues.append(f"{rel}: contains legacy decision-atoms projection wording; S4 must use propositions as primary input")
    if not _any_heading_present(text, "s5_headings.input_disposition", S4_INPUT_DISPOSITION_HEADING):
        issues.append(f"{rel}: missing section `{S4_INPUT_DISPOSITION_HEADING}`")
    if not _any_heading_present(text, "s5_headings.domain_model", S4_DOMAIN_MODEL_HEADING):
        issues.append(f"{rel}: missing section `{S4_DOMAIN_MODEL_HEADING}`")
    if not _any_heading_present(text, "s5_headings.ordering_rationale", S4_ORDER_PLAN_HEADING):
        issues.append(f"{rel}: missing section `{S4_ORDER_PLAN_HEADING}`")
    if not _any_heading_present(text, "s5_headings.closed_chains", S4_CLOSED_HEADING):
        issues.append(f"{rel}: missing section `{S4_CLOSED_HEADING}`")
        return issues
    if not _any_heading_present(text, "s5_headings.pending_adjudication", S4_UNRESOLVED_HEADING):
        issues.append(f"{rel}: missing section `{S4_UNRESOLVED_HEADING}`")
        return issues

    closed_part = text.split(_cl_h, 1)[1].split(_ur_h, 1)[0] if _cl_h and _ur_h else ""
    disposition_end_heading = _dm_h or _op_h or _cl_h or S4_CLOSED_HEADING
    disposition_part = (
        text.split(_id_h, 1)[1].split(disposition_end_heading, 1)[0]
        if _id_h and disposition_end_heading and _id_h in text and disposition_end_heading in text
        else ""
    )
    domain_model_part = (
        text.split(_dm_h, 1)[1].split(_op_h, 1)[0]
        if _dm_h and _op_h and _dm_h in text and _op_h in text
        else ""
    )
    order_plan_part = (
        text.split(_op_h, 1)[1].split(_cl_h, 1)[0]
        if _op_h and _cl_h and _op_h in text and _cl_h in text
        else ""
    )
    unresolved_part = text.split(_ur_h, 1)[1] if _ur_h and _ur_h in text else ""

    chain_count = sum(1 for ln in closed_part.splitlines() if S4_CHAIN_HEADING_RE.match(ln.strip()))
    if chain_count <= 0 and not S4_NO_CLOSED_CHAIN_RE.search(closed_part):
        issues.append(f"{rel}: closed section has no `### 链 n` entries")
    if chain_count > 0:
        issues.extend(_s4_order_plan_violations(rel, order_plan_part, closed_part))

    for token in ("contract_candidate", "evidence_note", "noise_context"):
        if token not in disposition_part:
            issues.append(f"{rel}: input disposition section missing `{token}` handling")
    if not S4_NORMALIZATION_DISPOSITION_RE.search(disposition_part):
        issues.append(f"{rel}: input disposition missing semantic normalization handling")
    if not S4_ORDER_DISPOSITION_RE.search(disposition_part):
        issues.append(f"{rel}: input disposition missing source/order normalization handling")
    if S4_ORDER_ARROW_RE.search(disposition_part) and "组织顺序说明" not in disposition_part:
        issues.append(f"{rel}: input disposition contains a detailed arrow order; use `## 组织顺序说明` as the single source of chain order")
    issues.extend(_s4_domain_model_violations(rel, domain_model_part, closed_part, unresolved_part))
    issues.extend(_s4_reciprocal_unresolved_link_violations(rel, closed_part, unresolved_part))

    for block in _s4_closed_chain_blocks(closed_part):
        if S4_HALF_CLOSED_GAP_RE.search(block) and not S4_LINKED_DECISION_RE.search(block):
            issues.append(f"{rel}: half-closed chain mentions gaps but lacks `关联待裁决：问题 N`")

    if S4_PLACEHOLDER_RE.search(closed_part):
        issues.append(f"{rel}: closed section contains placeholder wording (待补充/按来源/待确认对象)")

    if S4_UNRESOLVED_TOKEN_RE.search(closed_part):
        issues.append(f"{rel}: unresolved tokens appear inside closed section; move to `{S4_UNRESOLVED_HEADING}`")

    if S4_UNRESOLVED_TOKEN_RE.search(text) and not S4_UNRESOLVED_TOKEN_RE.search(unresolved_part):
        issues.append(f"{rel}: unresolved tokens exist but unresolved section does not capture them")
    for block in _s4_unresolved_blocks(unresolved_part):
        if not S4_UNRESOLVED_BINDING_RE.search(block):
            issues.append(f"{rel}: unresolved issue lacks `关联链：链 N` or `关联前置域：...` binding")
        if not S4_UNRESOLVED_IMPACT_RE.search(block):
            issues.append(f"{rel}: unresolved issue lacks `决策影响：...`")

    return issues


def _s4_domain_model_violations(
    rel: Path, domain_model_part: str, closed_part: str, unresolved_part: str
) -> list[str]:
    issues: list[str] = []
    if not domain_model_part.strip():
        return issues
    missing_terms = [term for term in S4_TYPED_MODEL_DIMENSIONS if term not in domain_model_part]
    if missing_terms:
        issues.append(f"{rel}: domain model missing required dimensions: {', '.join(missing_terms)}")
    if not S4_DOMAIN_MODEL_REQUIRED_RE.search(domain_model_part):
        issues.append(f"{rel}: domain model lacks typed model vocabulary")
    model_terms = _s4_typed_model_terms(domain_model_part)
    for line in domain_model_part.splitlines():
        m = S4_DOMAIN_OBJECT_LINE_RE.match(line.strip())
        if not m:
            continue
        object_line = m.group(1)
        if S4_DOMAIN_BOUNDARY_OBJECT_RE.search(object_line):
            issues.append(f"{rel}: domain object line includes boundary/excluded material; demote it from `领域对象`")
        if S4_DOMAIN_OBJECT_MIXED_LAYER_RE.search(object_line):
            issues.append(f"{rel}: domain object line includes metrics/fields/containers; demote them from `领域对象`")
    for idx, block in enumerate(_s4_closed_chain_blocks(closed_part), start=1):
        found = {m.group(1).replace(" ", "") for m in S4_CHAIN_MODEL_FIELD_RE.finditer(block)}
        required = {"领域对象", "状态变化", "业务动作"}
        if not required.issubset(found):
            missing = sorted(required - found)
            issues.append(f"{rel}: closed chain {idx} missing model binding fields: {', '.join(missing)}")
        if "展示容器/字段锚点" not in found and "展示容器" not in found and "字段锚点" not in found:
            issues.append(f"{rel}: closed chain {idx} missing display container / field anchor binding")
        issues.extend(_s4_chain_model_binding_violations(rel, idx, block, model_terms))
    return issues


def _s4_typed_model_terms(domain_model_part: str) -> dict[str, set[str]]:
    terms: dict[str, set[str]] = {"一等业务对象": set(), "指标/字段": set(), "展示容器": set()}
    for label, values in S4_MODEL_LINE_RE.findall(domain_model_part):
        terms.setdefault(label, set()).update(_split_model_terms(values))
    for label, values in _s4_section_model_terms(domain_model_part).items():
        terms.setdefault(label, set()).update(values)
    return terms


def _s4_section_model_terms(domain_model_part: str) -> dict[str, set[str]]:
    terms: dict[str, set[str]] = {"一等业务对象": set(), "指标/字段": set(), "展示容器": set()}
    matches = list(S4_MODEL_SECTION_RE.finditer(domain_model_part))
    for idx, match in enumerate(matches):
        label = match.group(1)
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(domain_model_part)
        block = domain_model_part[start:end]
        for line in block.splitlines():
            item = S4_MODEL_SECTION_ITEM_RE.match(line)
            if not item:
                continue
            value = _norm_model_section_item(item.group(1))
            if value:
                terms.setdefault(label, set()).add(value)
    return terms


def _norm_model_section_item(value: str) -> str:
    value = re.sub(r"\s+", " ", value.strip().strip("`").strip("*")).strip()
    if not value:
        return ""
    return _norm_model_term(value)


def _split_model_terms(values: str) -> set[str]:
    cleaned = values.strip().rstrip("。；;")
    if not cleaned:
        return set()
    parts = re.split(r"[、，,；;]", cleaned)
    return {_norm_model_term(part) for part in parts if _norm_model_term(part)}


def _norm_model_term(value: str) -> str:
    value = value.strip().strip("`").strip()
    return re.sub(r"\s+", " ", value).lower()


def _s4_chain_model_binding_violations(
    rel: Path, chain_idx: int, chain_block: str, model_terms: dict[str, set[str]]
) -> list[str]:
    issues: list[str] = []
    object_match = S4_CHAIN_OBJECT_LINE_RE.search(chain_block)
    if not object_match:
        return issues
    chain_objects = _split_model_terms(object_match.group(1))
    first_class = model_terms.get("一等业务对象") or set()
    metrics_or_fields = (model_terms.get("指标/字段") or set()) | (model_terms.get("展示容器") or set())
    for obj in sorted(chain_objects):
        if obj in first_class:
            continue
        if obj in metrics_or_fields or S4_DOMAIN_OBJECT_MIXED_LAYER_RE.search(obj):
            issues.append(
                f"{rel}: closed chain {chain_idx} uses metric/field/container as `领域对象` ({obj}); "
                "bind the chain to a first-class business object"
            )
        else:
            issues.append(
                f"{rel}: closed chain {chain_idx} `领域对象` ({obj}) is not listed in domain model `一等业务对象`"
            )
    return issues


def _s4_reciprocal_unresolved_link_violations(rel: Path, closed_part: str, unresolved_part: str) -> list[str]:
    issues: list[str] = []
    unresolved_by_id: dict[int, str] = {}
    for block in _s4_unresolved_blocks(unresolved_part):
        first_line = block.splitlines()[0].strip() if block.splitlines() else ""
        m = S4_UNRESOLVED_ID_RE.match(first_line)
        if m:
            unresolved_by_id[int(m.group(1))] = block

    for chain_idx, block in enumerate(_s4_closed_chain_blocks(closed_part), start=1):
        for ref in S4_UNRESOLVED_REF_RE.finditer(block):
            issue_id = int(ref.group(1))
            issue_block = unresolved_by_id.get(issue_id)
            if issue_block is None:
                issues.append(f"{rel}: chain {chain_idx} references missing unresolved issue {issue_id}")
                continue
            binding_match = S4_UNRESOLVED_CHAIN_BINDING_RE.search(issue_block)
            if not binding_match:
                issues.append(f"{rel}: unresolved issue {issue_id} referenced by chain {chain_idx} lacks reciprocal `关联链` binding")
                continue
            bound_chain_ids = {int(x) for x in re.findall(r"链\s*(\d+)", binding_match.group(1))}
            if chain_idx not in bound_chain_ids:
                issues.append(
                    f"{rel}: chain {chain_idx} references unresolved issue {issue_id}, "
                    f"but the issue binds chains {sorted(bound_chain_ids) or 'none'}"
                )
    return issues


def _s4_order_plan_violations(rel: Path, order_plan_part: str, closed_part: str) -> list[str]:
    issues: list[str] = []
    chains = _s4_chain_titles(closed_part)
    if not chains:
        return issues
    planned = _s4_planned_chain_titles(order_plan_part)
    if not planned:
        return [f"{rel}: order plan section does not list `链 N：标题 — 顺序理由` entries"]
    chain_ids = [idx for idx, _ in chains]
    planned_ids = [idx for idx, _ in planned]
    if planned_ids != chain_ids:
        issues.append(f"{rel}: order plan chain ids {planned_ids} do not match closed chain ids {chain_ids}")
        return issues
    for (chain_idx, chain_title), (_, planned_title) in zip(chains, planned):
        if _norm_title(chain_title) != _norm_title(planned_title):
            issues.append(
                f"{rel}: order plan title for 链 {chain_idx} does not match closed chain title "
                f"({planned_title!r} != {chain_title!r})"
            )
    return issues


def _s4_chain_titles(closed_part: str) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    for line in closed_part.splitlines():
        m = S4_CHAIN_TITLE_RE.match(line.strip())
        if m:
            out.append((int(m.group(1)), m.group(2).strip()))
    return out


def _s4_planned_chain_titles(order_plan_part: str) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    for line in order_plan_part.splitlines():
        m = S4_ORDER_PLAN_ITEM_RE.search(line.strip())
        if m:
            out.append((int(m.group(1)), m.group(2).strip()))
    return out


def _norm_title(s: str) -> str:
    return re.sub(r"\s+", "", s.strip().lower())


def _s4_closed_chain_blocks(closed_part: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    for line in closed_part.splitlines():
        if S4_CHAIN_HEADING_RE.match(line.strip()):
            if current:
                blocks.append("\n".join(current))
            current = [line]
            continue
        if current:
            current.append(line)
    if current:
        blocks.append("\n".join(current))
    return blocks


def _s4_unresolved_blocks(unresolved_part: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    for line in unresolved_part.splitlines():
        if S4_UNRESOLVED_HEADING_RE.match(line.strip()):
            if current:
                blocks.append("\n".join(current))
            current = [line]
            continue
        if current:
            current.append(line)
    if current:
        blocks.append("\n".join(current))
    return blocks




if __name__ == "__main__":
    sys.exit(main())
