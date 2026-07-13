#!/usr/bin/env python3
"""Dedicated S4 domain model quality gate.

This gate validates S4/S5 work drafts as explicit domain models. It does not
generate domain semantics; it only checks that Agent-authored semantics are
expressed in a stable, reviewable structure.
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
from distill.quality import S4_DOMAIN_MODEL_HEADING, S4_ORDER_PLAN_HEADING, _s4_structure_violations

FIRST_CLASS_SECTION_RE = re.compile(r"^###\s*一等业务对象\s*$", re.MULTILINE)
NEXT_THIRD_HEADING_RE = re.compile(r"^###\s+", re.MULTILINE)
FIRST_CLASS_ITEM_RE = re.compile(r"^\s*[-*]\s*(?:`([^`]+)`|([^:：\n]+))(?:[:：].*)?$")
FIELD_OR_CONTAINER_OBJECT_RE = re.compile(
    r"("
    r"(?i:\bapi\b|\bendpoint\b|\bfield\b|\bpage\b|\bcard\b|\blist\b|\bresponse\b)|"
    r"接口|字段|页面|卡片|列表|详情页|响应|公式|金额|进度|目标|路径|"
    r"\b[a-z][a-z0-9_]+_(?:id|status|amount|total|date|time|code|url|api)\b|"
    r"\b[a-z][A-Za-z0-9]*[A-Z][A-Za-z0-9]*(?:Id|Status|Amount|Total|Date|Time|Code|URL|Url|API)\b"
    r")"
)


def check_work_draft_text(path: Path, text: str) -> list[str]:
    """Return S4 domain-model issues for one work draft."""

    issues = list(_s4_structure_violations(path, text))
    issues.extend(_first_class_object_name_violations(path, text))
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


def _first_class_object_name_violations(path: Path, text: str) -> list[str]:
    section = _domain_model_section(text)
    first_class = _first_class_section(section)
    if not first_class.strip():
        return []
    rel = _rel(path)
    issues: list[str] = []
    for line in first_class.splitlines():
        match = FIRST_CLASS_ITEM_RE.match(line)
        if not match:
            continue
        name = (match.group(1) or match.group(2) or "").strip().strip("*").strip()
        if not name:
            continue
        if FIELD_OR_CONTAINER_OBJECT_RE.search(name):
            issues.append(
                f"{rel}: first-class object looks field/API/container-like ({name}); "
                "move it to `指标/字段` or `展示容器`"
            )
    return issues


def _domain_model_section(text: str) -> str:
    from runtime.deliverable_locale import all_locale_values as _all_locale
    dm_headings = _all_locale("s5_headings.domain_model") or [S4_DOMAIN_MODEL_HEADING]
    op_headings = _all_locale("s5_headings.ordering_rationale") or [S4_ORDER_PLAN_HEADING]
    dm_heading = next((h for h in dm_headings if h in text), None)
    if not dm_heading:
        return ""
    rest = text.split(dm_heading, 1)[1]
    for op_h in op_headings:
        if op_h in rest:
            return rest.split(op_h, 1)[0]
    next_second = re.search(r"\n##\s+", rest)
    return rest[: next_second.start()] if next_second else rest


def _first_class_section(domain_model_section: str) -> str:
    match = FIRST_CLASS_SECTION_RE.search(domain_model_section)
    if not match:
        return ""
    rest = domain_model_section[match.end() :]
    next_match = NEXT_THIRD_HEADING_RE.search(rest)
    return rest[: next_match.start()] if next_match else rest


def _rel(path: Path) -> Path | str:
    try:
        return path.relative_to(REPO_ROOT)
    except ValueError:
        return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Check S4 domain model structure and S5 model binding.")
    parser.add_argument("--root-id", help="Only check this curated root ID.")
    parser.add_argument("--warn-only", action="store_true", help="Print issues but exit 0.")
    args = parser.parse_args()

    issues = collect_issues(args.root_id)
    if issues:
        print("S4 domain model quality issues:", file=sys.stderr)
        for issue in issues:
            print(f"  {issue}", file=sys.stderr)
    print(f"S4 domain model quality: issues={len(issues)}")
    return 0 if not issues or args.warn_only else 1


if __name__ == "__main__":
    raise SystemExit(main())
