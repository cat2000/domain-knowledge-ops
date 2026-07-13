#!/usr/bin/env python3
"""Validate decision-atom artifacts for confirmed themes."""
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

from runtime.domain_knowledge_paths import CURATED_BY_ROOT, confirmed_slugs_from_checklist, resolve_checklist_file


def _contract_candidate_count(path: Path) -> int:
    if not path.is_file():
        return 0
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return 0
    total = 0
    for page in list(payload.get("pages") or []):
        for item in list(page.get("proposition_items") or []):
            if str(item.get("candidate_type") or "") == "contract_candidate":
                total += 1
    return total


def _valid_evidence_ref(curated_root: Path, ref: object) -> bool:
    value = str(ref or "").strip()
    if value.startswith("http"):
        return True
    if not value:
        return False
    repo = Path(__file__).resolve().parents[2]
    path = repo / value
    if path.is_file():
        return True
    # Jira closure paths are rooted at curated/by-root/<R>/.
    return (curated_root / value).is_file()


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Decision-atom quality gate.")
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
        agg = curated_root / "_aggregate" / slug
        json_path = agg / f"{slug}-decision-atoms.json"
        md_path = agg / f"{slug}-decision-atoms.md"
        if not json_path.is_file():
            issues.append(f"{json_path}: missing decision atoms json")
            continue
        if not md_path.is_file():
            issues.append(f"{md_path}: missing decision atoms markdown")
        try:
            payload = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            issues.append(f"{json_path}: invalid json ({e})")
            continue

        atoms = list(payload.get("atoms") or [])
        if not atoms:
            contract_count = _contract_candidate_count(agg / f"{slug}-propositions.json")
            if contract_count > 0:
                issues.append(f"{json_path}: atoms list is empty but propositions contain {contract_count} contract candidates")
            continue
        for idx, atom in enumerate(atoms, start=1):
            if atom.get("is_placeholder"):
                continue
            missing_fields = {
                str(x).strip()
                for x in list(atom.get("missing_fields") or [])
                if str(x).strip()
            }
            for key in ("actor", "condition", "branch_action", "observable_outcome", "time_window", "exception"):
                if not str(atom.get(key) or "").strip() and key not in missing_fields:
                    issues.append(f"{json_path}: atom#{idx} missing {key} without missing_fields marker")
            dq = str(atom.get("decision_question") or "").strip()
            if dq in {"", "UNKNOWN", "MIXED"}:
                issues.append(f"{json_path}: atom#{idx} invalid decision_question={dq or 'EMPTY'}")
            refs = atom.get("evidence_refs") or []
            if not refs or not any(_valid_evidence_ref(curated_root, r) for r in refs):
                issues.append(f"{json_path}: atom#{idx} missing valid evidence_refs")
            branch_ids = list(atom.get("branch_ids") or [])
            if branch_ids:
                if not str(atom.get("branch_condition") or "").strip():
                    issues.append(f"{json_path}: atom#{idx} missing branch_condition")
                if not str(atom.get("branch_outcome") or "").strip():
                    issues.append(f"{json_path}: atom#{idx} missing branch_outcome")
                if len(branch_ids) >= 2 and not str(atom.get("branch_list") or "").strip():
                    issues.append(f"{json_path}: atom#{idx} missing branch_list for multi-branch rule")

    if issues:
        print("Decision atom quality issues:", file=sys.stderr)
        for i in issues:
            print(f"  {i}", file=sys.stderr)
    print(f"Decision atom quality: checked_confirmed_slugs={checked} issues={len(issues)}")
    if issues and not args.warn_only:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
