"""Enumerate Confluence pages — orchestration (CQL or BFS → compact rows)."""

from __future__ import annotations

import json
import sys
from argparse import Namespace
from pathlib import Path
from typing import Any, Dict, List

from wiki.lib.enumerate_http import (
    ensure_enum_root_included,
    enumerate_descendants,
    search_pages_cql,
)
from wiki.lib.enumerate_logic import compact_row


def enumerate_to_compact(
    *,
    base_url: str,
    wiki_base: str,
    auth_header: str,
    root_id: str,
    cql: str,
    page_size: int,
    include_enum_root: bool,
) -> List[Dict[str, Any]]:
    """List pages (CQL or BFS), compact rows, optionally prepend enumeration root."""
    if cql:
        rows = search_pages_cql(base_url, auth_header, cql, page_size)
        print(f"cql: {len(rows)} page(s) (deduped)", file=sys.stderr)
    else:
        rows = enumerate_descendants(base_url, auth_header, root_id, page_size)
        print(f"root={root_id} bfs_descendants={len(rows)}", file=sys.stderr)

    compact = [compact_row(page, wiki_base) for page in rows]
    if include_enum_root:
        compact = ensure_enum_root_included(
            compact, base_url, auth_header, wiki_base, root_id
        )
        print(
            f"enumerate: after root merge, {len(compact)} page row(s)",
            file=sys.stderr,
        )
    return compact


def run_enumerate(args: Namespace) -> None:
    from runtime.atlassian_env import ConfluenceEnv, load_dotenv

    load_dotenv()
    conf = ConfluenceEnv.from_env(required=True)
    assert conf is not None
    auth = conf.auth_header()
    page_size = max(1, min(args.page_size, 250))

    compact = enumerate_to_compact(
        base_url=args.base_url,
        wiki_base=args.wiki_base,
        auth_header=auth,
        root_id=str(args.root),
        cql=(args.cql or "").strip(),
        page_size=page_size,
        include_enum_root=not args.no_include_enum_root,
    )

    if args.json:
        out_path = Path(args.json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(compact, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(
            f"Wrote {args.json} ({len(compact)} row(s)) — enumeration succeeded (exit 0).",
            file=sys.stderr,
        )
    else:
        for row in sorted(compact, key=lambda item: int(item["id"])):
            print(f'{row["id"]}\t{row.get("spaceKey", "")}\t{row["title"]}')
