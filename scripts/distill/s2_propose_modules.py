#!/usr/bin/env python3
"""S2 module proposal: Wiki tree + strategy industry seeds → S2_PROPOSED_MODULES.*"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SCRIPTS = next(p for p in Path(__file__).resolve().parents if (p / "_install.py").is_file())
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
import _install

_install.bootstrap(__file__)

from distill.s2_propose_modules_logic import (  # noqa: E402
    build_parent_map_bfs,
    load_page_records,
    propose_modules,
    render_checklist_draft,
    render_proposed_modules_md,
)
from runtime.atlassian_env import ConfluenceEnv, load_dotenv  # noqa: E402
from runtime.domain_knowledge_paths import CURATED_BY_ROOT, EXTRACTED_BY_ROOT  # noqa: E402
from runtime.domain_profiles import team_key_for_scope  # noqa: E402
from wiki.lib.enumerate_http import iter_child_pages  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Propose domain modules from Confluence Wiki tree + strategy-derived industry seeds "
            "(s2-propose-industry-seeds.json; may be empty until @setup-domain-ops). "
            "Outputs S2_PROPOSED_MODULES.json/.md for human review before profile config."
        )
    )
    parser.add_argument("--root-id", required=True, help="Confluence enumeration root page ID")
    parser.add_argument(
        "--no-wiki-tree",
        action="store_true",
        help="Skip Confluence REST parent walk (industry seeds + facets only)",
    )
    parser.add_argument(
        "--write-checklist-draft",
        action="store_true",
        help="Also write DOMAIN_MODULE_CHECKLIST.proposed.md with 待确认 rows",
    )
    return parser.parse_args()


def _load_descendants(extracted_root: Path) -> list[dict]:
    path = extracted_root / "descendants-full.json"
    if not path.is_file():
        path = extracted_root / "_subtree_enumeration.json"
    if not path.is_file():
        raise SystemExit(f"Missing descendants JSON under {extracted_root}")
    rows = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise SystemExit(f"Invalid descendants JSON: {path}")
    return rows


def _fetch_wiki_tree(root_id: str) -> tuple[dict[str, str | None], dict[str, str]]:
    load_dotenv()
    conf = ConfluenceEnv.from_env(required=True)
    if conf is None:
        raise SystemExit("ATLASSIAN_EMAIL + ATLASSIAN_API_TOKEN required for Wiki tree walk")
    auth = conf.auth_header()
    base = conf.wiki_base_url.rstrip("/")

    def iter_children(parent_id: str):
        yield from iter_child_pages(base, auth, parent_id, page_size=100)

    parent_by_child, _children_by_parent, title_by_id = build_parent_map_bfs(
        root_id=root_id,
        iter_children=iter_children,
    )
    return parent_by_child, title_by_id


def main() -> int:
    args = _parse_args()
    root_id = str(args.root_id).strip()
    extracted_root = EXTRACTED_BY_ROOT / root_id
    curated_root = CURATED_BY_ROOT / root_id
    if not extracted_root.is_dir():
        print(f"Missing extracted root: {extracted_root}", file=sys.stderr)
        return 1

    descendants = _load_descendants(extracted_root)
    pages = load_page_records(descendants, extracted_root / "pages")

    parent_by_child: dict[str, str | None] | None = None
    title_by_id: dict[str, str] | None = None
    if not args.no_wiki_tree:
        try:
            parent_by_child, title_by_id = _fetch_wiki_tree(root_id)
            print(
                f"s2_propose_modules: wiki tree mapped {len(parent_by_child) - 1} page(s) under root {root_id}",
                file=sys.stderr,
            )
        except SystemExit:
            raise
        except Exception as exc:
            print(
                f"s2_propose_modules: wiki tree walk failed ({exc}); "
                "retry with credentials or pass --no-wiki-tree",
                file=sys.stderr,
            )
            return 1

    team_key = team_key_for_scope(root_id)
    if not team_key:
        print(
            f"s2_propose_modules: root {root_id} not in team-roots.json; "
            "industry seeds with teams[] will be skipped",
            file=sys.stderr,
        )
    payload = propose_modules(
        root_id=root_id,
        pages=pages,
        parent_by_child=parent_by_child,
        title_by_id=title_by_id,
        team_key=team_key,
    )

    curated_root.mkdir(parents=True, exist_ok=True)
    json_path = curated_root / "S2_PROPOSED_MODULES.json"
    md_path = curated_root / "S2_PROPOSED_MODULES.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_proposed_modules_md(payload), encoding="utf-8")

    if args.write_checklist_draft:
        draft_path = curated_root / "DOMAIN_MODULE_CHECKLIST.proposed.md"
        draft_path.write_text(render_checklist_draft(payload), encoding="utf-8")
        print(f"Wrote {draft_path.relative_to(curated_root.parents[2])}", file=sys.stderr)

    module_count = len(payload.get("proposed_modules") or [])
    print(
        f"s2_propose_modules complete: root_id={root_id} pages={payload.get('page_total', 0)} "
        f"proposed_modules={module_count} → {json_path.name}, {md_path.name}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
