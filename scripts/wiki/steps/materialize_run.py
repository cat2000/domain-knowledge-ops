"""Materialize extracted pages → materialized/*.md orchestration."""

from __future__ import annotations

import sys
import json
from argparse import Namespace
from collections import defaultdict
from pathlib import Path
from typing import Any, DefaultDict, Dict, List, Tuple

from runtime.paths import REPO_ROOT

from wiki.lib.materialize_logic import (
    is_skip_outline,
    parse_frontmatter,
    polish_rule_body,
    render_materialized_markdown,
    safe_rules_path,
    strip_extract_heading,
)

LEGACY_PRODUCT_DIRS = {
    "hui": (
        REPO_ROOT / "domain-knowledge/extracted/by-root/48694645/pages",
        REPO_ROOT / "domain-knowledge/materialized/by-root/48694645",
    ),
    "mall": (
        REPO_ROOT / "domain-knowledge/extracted/by-root/48696506/pages",
        REPO_ROOT / "domain-knowledge/materialized/by-root/48696506",
    ),
}


def materialize(product: str) -> Tuple[int, int]:
    extracted_root, rules_base = LEGACY_PRODUCT_DIRS[product]
    return materialize_dirs(extracted_root, rules_base)


MANIFEST_FILE = "_materialized_manifest.json"


def materialize_dirs(extracted_root: Path, rules_base: Path) -> Tuple[int, int]:
    if not extracted_root.is_dir():
        raise SystemExit(f"Missing extracted dir: {extracted_root}")

    groups: DefaultDict[str, List[Dict[str, Any]]] = defaultdict(list)
    pages_skipped = 0
    page_sources_by_target: dict[str, list[str]] = defaultdict(list)

    for path in sorted(extracted_root.glob("*.md")):
        if path.name == "README.md":
            continue
        front_matter, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        kb_outline_path = front_matter.get("kb_outline", "")
        if is_skip_outline(str(kb_outline_path)):
            pages_skipped += 1
            continue
        try:
            safe_rules_path(rules_base, str(kb_outline_path))
        except ValueError as error:
            print(f"Skip {path.name}: {error}", file=sys.stderr)
            pages_skipped += 1
            continue
        rel = str(kb_outline_path)
        groups[rel].append(
            {
                "page_id": front_matter.get("page_id", path.stem),
                "title": front_matter.get("title", path.stem),
                "web_ui": front_matter.get("web_ui", ""),
                "body": polish_rule_body(strip_extract_heading(body)),
            }
        )
        page_sources_by_target[rel].append(path.stem)

    if not groups and pages_skipped > 0:
        print(
            "materialize_rules_from_extracted: only kb_outline — (generic root); "
            "using auto-scan/<page_id>.md per page",
            file=sys.stderr,
        )
        pages_skipped = 0
        for path in sorted(extracted_root.glob("*.md")):
            if path.name == "README.md":
                continue
            front_matter, body = parse_frontmatter(path.read_text(encoding="utf-8"))
            kb_outline_path = f"auto-scan/{path.stem}.md"
            rel = str(kb_outline_path)
            groups[rel].append(
                {
                    "page_id": front_matter.get("page_id", path.stem),
                    "title": front_matter.get("title", path.stem),
                    "web_ui": front_matter.get("web_ui", ""),
                    "body": polish_rule_body(strip_extract_heading(body)),
                }
            )
            page_sources_by_target[rel].append(path.stem)

    files_written = 0
    current_targets: set[str] = set()
    for rel, pages in sorted(groups.items()):
        pages.sort(key=lambda page: int(str(page["page_id"])))
        target = safe_rules_path(rules_base, rel)
        current_targets.add(rel)
        stem_title = target.stem.replace("-", " ").replace("_", " ").title()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            render_materialized_markdown(stem_title, pages),
            encoding="utf-8",
        )
        files_written += 1
        print(
            f"Wrote {repo_rel(target)} ({len(pages)} pages)",
            file=sys.stderr,
        )

    stale_deleted = cleanup_stale_materialized_files(rules_base, current_targets)
    write_materialized_manifest(
        rules_base,
        extracted_root,
        current_targets,
        page_sources_by_target,
        files_written,
        pages_skipped,
        stale_deleted,
    )
    return files_written, pages_skipped


def repo_rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def cleanup_stale_materialized_files(rules_base: Path, current_targets: set[str]) -> int:
    """Delete generated materialized Markdown files no longer present in the current source set."""
    if not rules_base.exists():
        return 0
    keep = {str(Path(rel).as_posix()) for rel in current_targets}
    deleted = 0
    for path in sorted(rules_base.rglob("*.md")):
        if path.name.upper() == "README.MD":
            continue
        try:
            rel = path.relative_to(rules_base).as_posix()
        except ValueError:
            continue
        if rel in keep:
            continue
        path.unlink()
        deleted += 1
    remove_empty_dirs(rules_base)
    return deleted


def remove_empty_dirs(root: Path) -> None:
    if not root.exists():
        return
    for path in sorted((p for p in root.rglob("*") if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
        try:
            path.rmdir()
        except OSError:
            pass


def write_materialized_manifest(
    rules_base: Path,
    extracted_root: Path,
    current_targets: set[str],
    page_sources_by_target: dict[str, list[str]],
    files_written: int,
    pages_skipped: int,
    stale_deleted: int,
) -> None:
    rules_base.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "extracted_dir": str(extracted_root),
        "files_written": files_written,
        "pages_skipped": pages_skipped,
        "stale_deleted": stale_deleted,
        "targets": [
            {
                "path": rel,
                "source_page_ids": sorted(
                    set(page_sources_by_target.get(rel, [])),
                    key=lambda x: (0, int(x)) if x.isdigit() else (1, x),
                ),
            }
            for rel in sorted(current_targets)
        ],
    }
    (rules_base / MANIFEST_FILE).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def run_materialize(args: Namespace) -> None:
    if args.product:
        files_written, pages_skipped = materialize(args.product)
        tag = args.product
    else:
        if not args.rules_base:
            raise SystemExit("--rules-base is required with --extracted-dir")
        files_written, pages_skipped = materialize_dirs(
            args.extracted_dir,
            args.rules_base,
        )
        tag = args.root_page_id or args.extracted_dir.name

    print(
        f"materialize_rules_from_extracted [{tag}]: "
        f"{files_written} rule files written, {pages_skipped} extracted pages skipped (— or unsafe path)",
        file=sys.stderr,
    )
