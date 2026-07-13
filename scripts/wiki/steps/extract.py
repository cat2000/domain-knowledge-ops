#!/usr/bin/env python3
"""
Fetch Confluence page bodies for a descendants JSON via REST (any team root).

Use **`--workers N`** or **`CONFLUENCE_EXTRACT_WORKERS`** for parallel page fetches (thread pool).
Sequential pacing **`--sleep`** applies only when **`--workers` is 1** (default). Watch for HTTP 429 if N is high.

Default: Mall APP → `extracted/by-root/48696506/pages` + `facet_classify.classify`.

  python3 scripts/wiki/steps/extract.py --json-path …/descendants-full.json --out-dir …/pages
  python3 scripts/wiki/steps/extract.py --hui   # legacy: Hui → extracted/by-root/48694645/pages
  python3 scripts/wiki/steps/extract.py --limit 5
  python3 scripts/wiki/steps/extract.py --hui --fetch-attachments

**附件**：`--fetch-attachments` 全量拉附件；**`--attachment-pages ID,ID`** 仅指定页；
**`--attachment-subroot ID`** 拉该页及其全部后代（BFS）。可与 **`--fetch-attachments`** 组合（有限集合优先生效）。

YAML front matter uses `classify(title, body_snippet)` when the classify module
supports it (正文片段用于标题归类偏弱时的启发式); **kb_outline** is
“—” for non-business pages (same scope policy as Mall).

Auth: ATLASSIAN_EMAIL + ATLASSIAN_API_TOKEN; optional repo-root `.env`.
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

from _bootstrap import REPO_ROOT, SCRIPTS_DIR
from wiki.lib.extract_logic import auto_extract_workers
from wiki.steps.extract_run import run_extract


MALL_JSON = REPO_ROOT / "domain-knowledge/extracted/by-root/48696506/descendants-full.json"
MALL_OUT = REPO_ROOT / "domain-knowledge/extracted/by-root/48696506/pages"

HUI_JSON = REPO_ROOT / "domain-knowledge/extracted/by-root/48694645/descendants-full.json"
HUI_OUT = REPO_ROOT / "domain-knowledge/extracted/by-root/48694645/pages"

DEFAULT_CLASSIFY = SCRIPTS_DIR / "wiki/lib/facet_classify.py"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract Confluence page bodies for Mall or Hui descendant JSON."
    )
    parser.add_argument(
        "--hui",
        action="store_true",
        help="Shorthand for Hui App (JSON/out/classify/README)",
    )
    parser.add_argument(
        "--json-path",
        type=Path,
        default=None,
        help="Descendants JSON (default: Mall or Hui when --hui)",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Output directory for per-page .md files",
    )
    parser.add_argument(
        "--classify-module",
        type=Path,
        default=None,
        help="Python file exporting classify(title[, body_snippet])->(theme, kb_path)",
    )
    parser.add_argument(
        "--product-name",
        default=None,
        help="Product label for generated README (e.g. Mall APP)",
    )
    parser.add_argument(
        "--confluence-root-url",
        default=None,
        help="Link shown in generated README",
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get(
            "CONFLUENCE_BASE_URL", "https://your-site.atlassian.net/wiki"
        ),
        help="Wiki base URL including /wiki",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.15,
        help="Seconds between API requests (sequential mode only; ignored when --workers > 1)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        metavar="N",
        help=(
            "Parallel page fetches (thread pool). "
            "Default: CONFLUENCE_EXTRACT_WORKERS, else derived from JSON row count "
            "(see auto_extract_workers). "
            ">1 skips --sleep pacing between pages; reduce workers if Confluence returns HTTP 429."
        ),
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Only process first N pages (0 = all)",
    )
    parser.add_argument(
        "--fetch-attachments",
        action="store_true",
        help=(
            "List/download page attachments and append extracted text (txt/md/csv/json/xlsx/pdf…); "
            "unknown types are recorded in attachment-type-inventory.json."
        ),
    )
    parser.add_argument(
        "--attachment-max-bytes",
        type=int,
        default=int(os.environ.get("CONFLUENCE_ATTACHMENT_MAX_BYTES", "15728640")),
        help="Skip attachment bodies larger than this (default 15MB).",
    )
    parser.add_argument(
        "--attachment-inventory",
        type=Path,
        default=None,
        help=(
            "JSON path merging seen attachment extensions / outcomes "
            "(default: <out-dir-parent>/attachment-type-inventory.json)"
        ),
    )
    parser.add_argument(
        "--attachment-pages",
        default="",
        help=(
            "Comma-separated page IDs: download attachments only for these pages "
            "(also scans body markup). Does not require --fetch-attachments. "
            "Env: CONFLUENCE_ATTACHMENT_PAGES."
        ),
    )
    parser.add_argument(
        "--attachment-subroot",
        default="",
        help=(
            "Page ID: download attachments for this page and all descendants (REST BFS). "
            "Does not require --fetch-attachments. Env: CONFLUENCE_ATTACHMENT_SUBROOT."
        ),
    )
    parser.add_argument(
        "--write-report",
        type=Path,
        default=None,
        metavar="PATH",
        help=(
            "Write JSON with enumerated_page_count, page_ids, errors[{page_id, message}]. "
            "For orchestrator summaries."
        ),
    )
    args = parser.parse_args()
    if not (args.attachment_pages or "").strip():
        args.attachment_pages = os.environ.get("CONFLUENCE_ATTACHMENT_PAGES", "")
    if not (args.attachment_subroot or "").strip():
        args.attachment_subroot = os.environ.get("CONFLUENCE_ATTACHMENT_SUBROOT", "")

    if args.hui:
        args.json_path = args.json_path or HUI_JSON
        args.out_dir = args.out_dir or HUI_OUT
        args.classify_module = args.classify_module or DEFAULT_CLASSIFY
        args.product_name = args.product_name or "Hui App"
        args.confluence_root_url = (
            args.confluence_root_url
            or "https://your-site.atlassian.net/wiki/spaces/ALPHA/pages/48694645/Demo+App+A"
        )
    else:
        args.json_path = args.json_path or MALL_JSON
        args.out_dir = args.out_dir or MALL_OUT
        args.classify_module = args.classify_module or DEFAULT_CLASSIFY
        args.product_name = args.product_name or "Mall APP"
        args.confluence_root_url = (
            args.confluence_root_url
            or "https://your-site.atlassian.net/wiki/spaces/ALPHA/pages/48696506/Demo+App+B"
        )

    run_extract(args, repo_root=REPO_ROOT)


if __name__ == "__main__":
    main()
