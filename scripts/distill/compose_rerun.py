#!/usr/bin/env python3
"""Compose-stage orchestrator without S4/S5/S6 template fallback."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

_SCRIPTS = next(p for p in Path(__file__).resolve().parents if (p / "_install.py").is_file())
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
import _install

_install.bootstrap(__file__)

from runtime.domain_knowledge_paths import CHECKLIST_STATUS_CONFIRMED, CURATED_BY_ROOT, is_checklist_status_confirmed, resolve_checklist_file

_DELIVER_SLUG_RE = re.compile(r"_deliver/([a-z0-9-]+)/")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compose-stage orchestrator for confirmed Wiki slugs.")
    parser.add_argument("--root-id", required=True, help="Confluence root page ID")
    parser.add_argument(
        "--stage",
        default="all",
        choices=["all", "s3_build", "s4_work_draft", "s6_final_draft"],
        help="Run a single Compose stage or the full script-checkable sequence.",
    )
    return parser.parse_args()


def _run(repo: Path, script: str, args: list[str]) -> None:
    cmd = [sys.executable, str(repo / "scripts" / script), *args]
    subprocess.run(cmd, check=True)


def _confirmed_slugs(checklist_text: str) -> list[str]:
    from runtime.domain_knowledge_paths import confirmed_slugs_from_checklist

    return confirmed_slugs_from_checklist(checklist_text)


def _build_aggregate_index(curated_root: Path, slug: str) -> None:
    props_json = curated_root / "_aggregate" / slug / f"{slug}-propositions.json"
    if not props_json.is_file():
        return
    payload = json.loads(props_json.read_text(encoding="utf-8"))
    lines = [
        f"# {slug}-聚合索引",
        "",
        "## 领域概述",
        "- 本页展示 S3 结构化来源索引，不承载 S4/S5 语义裁决。",
        "",
        "## 来源页索引",
    ]
    for i, page in enumerate(payload.get("pages", []), start=1):
        title = page.get("title", "")
        url = page.get("source_url", "")
        lines.append(f"- {i}. [{title}]({url})")
    out = curated_root / "_aggregate" / slug / f"{slug}-聚合索引.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _require_existing(deliver_dir: Path, pattern: str, stage_name: str, slug: str) -> None:
    files = sorted(deliver_dir.glob(pattern))
    valid = [p for p in files if p.is_file() and p.read_text(encoding="utf-8", errors="replace").strip()]
    if not valid:
        raise SystemExit(f"{stage_name}: missing required artifact for slug={slug} pattern={pattern}")


def _require_fresh_work_draft(curated_root: Path, slug: str) -> None:
    deliver_dir = curated_root / "_deliver" / slug
    files = sorted(deliver_dir.glob("*领域知识-工作稿.md"))
    valid = [p for p in files if p.is_file() and p.read_text(encoding="utf-8", errors="replace").strip()]
    if not valid:
        raise SystemExit(f"s4_work_draft: missing required artifact for slug={slug} pattern=*领域知识-工作稿.md")
    props = curated_root / "_aggregate" / slug / f"{slug}-propositions.json"
    if not props.is_file():
        raise SystemExit(f"s4_work_draft: missing S4 primary input for slug={slug}: {props}")
    newest_draft = max(valid, key=lambda p: p.stat().st_mtime)
    if newest_draft.stat().st_mtime < props.stat().st_mtime:
        raise SystemExit(
            "s4_work_draft: stale work draft for "
            f"slug={slug}; regenerate S4/S5 from propositions/命题清单 before continuing"
        )


def _run_s3_build(repo: Path, root_id: str, curated_root: Path) -> None:
    _run(repo, "distill/s2_recognize.py", ["--root-id", root_id])
    _run(repo, "distill/proposition_extract.py", ["--root-id", root_id])
    _run(repo, "distill/decision_atom_sync.py", ["--root-id", root_id])
    _run(repo, "distill/conflict_ledger_sync.py", ["--root-id", root_id])

    checklist = resolve_checklist_file(curated_root)
    if checklist is None:
        raise SystemExit(f"s3_build: missing checklist at {curated_root / 'DOMAIN_MODULE_CHECKLIST.md'}")
    for slug in _confirmed_slugs(checklist.read_text(encoding="utf-8", errors="replace")):
        _build_aggregate_index(curated_root, slug)


def _check_s4_work_draft(curated_root: Path) -> None:
    checklist = resolve_checklist_file(curated_root)
    if checklist is None:
        raise SystemExit(f"s4_work_draft: missing checklist at {curated_root / 'DOMAIN_MODULE_CHECKLIST.md'}")
    for slug in _confirmed_slugs(checklist.read_text(encoding="utf-8", errors="replace")):
        _require_fresh_work_draft(curated_root, slug)


def _check_s6_final_draft(curated_root: Path) -> None:
    checklist = resolve_checklist_file(curated_root)
    if checklist is None:
        raise SystemExit(f"s6_final_draft: missing checklist at {curated_root / 'DOMAIN_MODULE_CHECKLIST.md'}")
    for slug in _confirmed_slugs(checklist.read_text(encoding="utf-8", errors="replace")):
        deliver_dir = curated_root / "_deliver" / slug
        _require_existing(deliver_dir, "*领域知识定稿.md", "s6_final_draft", slug)


def main() -> int:
    args = _parse_args()
    root_id = str(args.root_id).strip()
    repo = Path(__file__).resolve().parents[2]
    curated_root = CURATED_BY_ROOT / root_id
    stage = str(args.stage or "all")

    if stage in {"all", "s3_build"}:
        _run_s3_build(repo, root_id, curated_root)
    if stage in {"all", "s4_work_draft"}:
        _check_s4_work_draft(curated_root)
    if stage in {"all", "s6_final_draft"}:
        _check_s6_final_draft(curated_root)
    print(f"Compose rerun complete for root_id={root_id} stage={stage}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
