#!/usr/bin/env python3
"""Validate conflict-ledger artifacts for confirmed themes."""
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

from runtime.domain_knowledge_paths import CURATED_BY_ROOT, confirmed_slugs_from_checklist, resolve_checklist_file


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Conflict ledger quality gate.")
    p.add_argument("--root-id", required=True, help="Confluence root page ID")
    p.add_argument("--warn-only", action="store_true")
    return p.parse_args()


def _confirmed_slugs(text: str) -> list[str]:
    return confirmed_slugs_from_checklist(text)


def main() -> int:
    args = _parse_args()
    root_id = str(args.root_id).strip()
    curated_root = CURATED_BY_ROOT / root_id
    checklist = resolve_checklist_file(curated_root)
    if checklist is None:
        print(f"Missing checklist: {curated_root / 'DOMAIN_MODULE_CHECKLIST.md'}", file=sys.stderr)
        return 0 if args.warn_only else 1

    issues: list[str] = []
    checked = 0
    for slug in _confirmed_slugs(checklist.read_text(encoding="utf-8", errors="replace")):
        checked += 1
        ledger = curated_root / "_aggregate" / slug / f"{slug}-conflict-ledger.md"
        if not ledger.is_file():
            issues.append(f"{ledger}: missing conflict ledger")
            continue
        text = ledger.read_text(encoding="utf-8", errors="replace")
        if "## 已裁决冲突" not in text:
            issues.append(f"{ledger}: missing '## 已裁决冲突' section")
        if "## 待确认冲突" not in text:
            issues.append(f"{ledger}: missing '## 待确认冲突' section")
        if "冲突项：" not in text and "无显式冲突" not in text:
            issues.append(f"{ledger}: no conflict entries nor explicit '无显式冲突'")

    if issues:
        print("Conflict ledger quality issues:", file=sys.stderr)
        for i in issues:
            print(f"  {i}", file=sys.stderr)
    print(f"Conflict ledger quality: checked_confirmed_slugs={checked} issues={len(issues)}")
    if issues and not args.warn_only:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
