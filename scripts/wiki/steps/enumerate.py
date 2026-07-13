#!/usr/bin/env python3
"""
Enumerate Confluence pages in two ways:

**Exit status:** **0** means the run finished and any ``--json`` output is **complete** for
that query. **Non-zero** means **enumeration failed** (auth, HTTP, or network/SSL timeout) —
**do not** treat an existing JSON file as authoritative; re-run after fixing connectivity or
credentials. Callers and humans must check ``exit code``, not only whether a path exists.

**Why enumerate:** produce ``descendants-full.json`` — the **pages to sync** under an
enumeration root (KB: extract + coverage). Each row is compact: ``id``, ``title``,
``spaceKey``, ``webUi`` only (no body text here; bodies are fetched later).

The **root page itself** (Space 首页 / 粘贴的根页) is **included** by default: BFS only
listed descendants before; CQL ``ancestor = X`` does not return ``X``. After listing,
the script fetches ``--root`` once and prepends it if missing (disable with
``--no-include-enum-root``).

1. **BFS** — REST `content/{id}/child/page`. Descendants only in the walk; root merged in after.
2. **CQL + pagination** — ``GET /rest/api/content/search?cql=...`` — use
   ``(id = ROOT OR ancestor = ROOT)`` in auto queries to include the root; merge step still
   guarantees the root row when `--root` is set.

Use `--cql` for search mode; omit it for BFS (requires `--root`).

Auth (Cloud): HTTP Basic with email + API token.

  export ATLASSIAN_EMAIL='you@company.com'
  export ATLASSIAN_API_TOKEN='your_api_token'

Or put the same keys in a repo-root `.env` (gitignored); existing OS env wins.

Optional:

  export CONFLUENCE_BASE_URL='https://YOUR_SITE.atlassian.net/wiki'

Default root for Mall APP KB work: 48696506.

Examples:

  python3 scripts/wiki/steps/enumerate.py --root 48696506
  python3 scripts/wiki/steps/enumerate.py --root 48694645 --json domain-knowledge/extracted/by-root/48694645/descendants-full.json
  python3 scripts/wiki/steps/enumerate.py --cql 'space = CMA AND type = page AND ancestor = 48694645 ORDER BY title' --json out.json
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_SCRIPTS = next(p for p in Path(__file__).resolve().parents if (p / "_install.py").is_file())
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
import _install

_install.bootstrap(__file__)

from wiki.lib.enumerate_http import enumerate_descendants  # noqa: F401 — extract_run import
from wiki.steps.enumerate_run import enumerate_to_compact, run_enumerate  # noqa: F401


def main() -> None:
    parser = argparse.ArgumentParser(
        description="List Confluence pages: BFS from --root, or CQL search with --cql."
    )
    parser.add_argument(
        "--root",
        default=os.environ.get("CONFLUENCE_ROOT_PAGE_ID", "48696506"),
        help="Root page id for BFS mode (ignored when --cql is set). Default 48696506 or CONFLUENCE_ROOT_PAGE_ID.",
    )
    parser.add_argument(
        "--cql",
        default="",
        help=(
            "If set, use paginated CQL search instead of BFS. Example: "
            "'space = CMA AND type = page AND ancestor = 48694645 ORDER BY title'"
        ),
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get(
            "CONFLUENCE_BASE_URL", "https://your-site.atlassian.net/wiki"
        ),
        help="Wiki base URL including /wiki (or CONFLUENCE_BASE_URL)",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=100,
        help="Child listing page size (max depends on site; try 100–250)",
    )
    parser.add_argument(
        "--json",
        metavar="FILE",
        help="Write full JSON array of compact rows to FILE",
    )
    parser.add_argument(
        "--wiki-base",
        default=os.environ.get(
            "CONFLUENCE_BASE_URL", "https://your-site.atlassian.net/wiki"
        ),
        help="Wiki base URL including /wiki — used with _links.webui (default: CONFLUENCE_BASE_URL)",
    )
    parser.add_argument(
        "--no-include-enum-root",
        action="store_true",
        help=(
            "Skip merging the --root page into the JSON. Default: include root "
            "(needed because CQL ancestor= excludes it; BFS listing excluded it too)."
        ),
    )
    run_enumerate(parser.parse_args())


if __name__ == "__main__":
    main()
