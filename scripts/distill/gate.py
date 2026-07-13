#!/usr/bin/env python3
"""Distill gate for Wiki outputs (S2 -> S6 consistency + distill checks)."""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

_SCRIPTS = next(p for p in Path(__file__).resolve().parents if (p / "_install.py").is_file())
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
import _install

_install.bootstrap(__file__)

from _bootstrap import REPO_ROOT, SCRIPTS_DIR
from runtime.domain_knowledge_paths import (
    CURATED_BY_ROOT,
    EXTRACTED_BY_ROOT,
    is_checklist_status_confirmed,
    resolve_checklist_file,
    resolve_closure_file,
)

_BACKTICK_PATH_RE = re.compile(r"`([^`]+)`")
_DELIVER_SLUG_RE = re.compile(r"_deliver/([^/]+)/")


@dataclass(frozen=True)
class ChecklistRow:
    theme: str
    main_entry: str
    status: str
    raw: str


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="One-shot distill gate for generate-knowledge-from-wiki outputs."
    )
    parser.add_argument("--root-id", help="Confluence root page ID.")
    from teams.registry import add_team_argument

    add_team_argument(parser, use_default=False)
    parser.add_argument(
        "--skip-domain-check",
        "--skip-kb-check",
        dest="skip_domain_check",
        action="store_true",
        help="Only run preflight structure checks, skip domain_check distill.",
    )
    return parser.parse_args()


def _resolve_root_id(team: str | None, root_id: str | None) -> str:
    if root_id:
        return str(root_id).strip()
    if not team:
        raise SystemExit("run_distill_gate: provide --root-id or --team")
    from teams.registry import resolve_team

    _, cfg = resolve_team(team)
    root_id_value = str(cfg.get("root_id") or "").strip()
    if not root_id_value:
        raise SystemExit(f"run_distill_gate: no root_id configured for team {team!r}")
    return root_id_value


def _parse_checklist_rows(text: str) -> list[ChecklistRow]:
    from runtime.checklist_modules import parse_checklist_modules

    rows: list[ChecklistRow] = []
    for mod in parse_checklist_modules(text):
        rows.append(
            ChecklistRow(
                theme=mod.theme,
                main_entry=mod.main_entry,
                status=mod.status,
                raw=mod.raw,
            )
        )
    return rows


def _extract_path(cell_text: str) -> str:
    match = _BACKTICK_PATH_RE.search(cell_text)
    if match:
        return match.group(1).strip()
    return cell_text.strip()


def _resolve_main_entry_path(main_entry: str, curated_root: Path) -> Path:
    path = Path(main_entry)
    if path.is_absolute():
        return path
    if main_entry.startswith("domain-knowledge/"):
        return REPO_ROOT / main_entry
    if main_entry.startswith("_deliver/") or main_entry.startswith("_附录/"):
        return curated_root / main_entry
    return REPO_ROOT / main_entry


def _collect_issues(root_id: str) -> list[str]:
    issues: list[str] = []
    curated_root = CURATED_BY_ROOT / root_id
    extracted_root = EXTRACTED_BY_ROOT / root_id

    if not curated_root.is_dir():
        return [f"missing curated root: {curated_root}"]

    handoff = extracted_root / "PIPELINE_HANDOFF.json"
    if not handoff.is_file():
        issues.append(f"missing handoff: {handoff}")

    checklist = resolve_checklist_file(curated_root)
    if checklist is None:
        issues.append(f"missing checklist: {curated_root / 'DOMAIN_MODULE_CHECKLIST.md'}")
        return issues

    closure = resolve_closure_file(curated_root)
    if closure is None:
        issues.append(f"missing closure: {curated_root / '_materialization_closure.json'}")

    text = checklist.read_text(encoding="utf-8", errors="replace")
    rows = _parse_checklist_rows(text)
    confirmed_rows = [row for row in rows if is_checklist_status_confirmed(row.status)]
    if not confirmed_rows:
        issues.append(f"{checklist}: no confirmed rows")
        return issues

    for row in confirmed_rows:
        main_entry = _extract_path(row.main_entry)
        if not main_entry:
            issues.append(f"{checklist}: confirmed row missing main entry path: {row.raw}")
            continue
        entry_path = _resolve_main_entry_path(main_entry, curated_root)
        if not entry_path.is_file():
            issues.append(f"{checklist}: main entry path missing: {main_entry}")
            continue
        match = _DELIVER_SLUG_RE.search(main_entry)
        if not match:
            issues.append(f"{checklist}: cannot infer deliver slug from main entry: {main_entry}")
            continue
        slug_dir = curated_root / "_deliver" / match.group(1)
        # Accept locale-brief (final draft) files from any deliverable_locale.
        try:
            from runtime.deliverable_locale import locale_brief_globs as _lbg
            _globs = _lbg() or ["*领域知识定稿.md"]
        except ImportError:
            _globs = ["*领域知识定稿.md"]
        final_drafts = sorted(p for g in _globs for p in slug_dir.glob(g))
        if not final_drafts:
            issues.append(
                f"{checklist}: confirmed theme '{row.theme}' has no S6 final draft in {slug_dir}"
            )
    return issues


def _run_domain_check(root_id: str) -> int:
    cmd = [sys.executable, str(SCRIPTS_DIR / "domain_check.py"), "distill", "--root-id", root_id]
    print("+", " ".join(cmd), file=sys.stderr)
    return subprocess.run(cmd, cwd=str(REPO_ROOT)).returncode


def _update_glossary(root_id: str) -> int:
    cmd = [sys.executable, str(SCRIPTS_DIR / "distill/glossary_update.py"), "--root-id", root_id]
    print("+", " ".join(cmd), file=sys.stderr)
    return subprocess.run(cmd, cwd=str(REPO_ROOT)).returncode


def main() -> int:
    args = _parse_args()
    root_id = _resolve_root_id(args.team, args.root_id)
    issues = _collect_issues(root_id)
    if issues:
        print("distill gate preflight failed:", file=sys.stderr)
        for msg in issues:
            print(f"  {msg}", file=sys.stderr)
        return 1

    if args.skip_domain_check:
        print(f"Distill gate preflight OK for root_id={root_id} (domain_check skipped).")
        return 0

    exit_code = _run_domain_check(root_id)
    if exit_code != 0:
        print(f"Distill gate failed at domain_check distill (root_id={root_id}).", file=sys.stderr)
        return exit_code
    glossary_exit_code = _update_glossary(root_id)
    if glossary_exit_code != 0:
        print(f"Distill gate failed while updating glossary (root_id={root_id}).", file=sys.stderr)
        return glossary_exit_code
    print(f"Distill gate passed for root_id={root_id}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
