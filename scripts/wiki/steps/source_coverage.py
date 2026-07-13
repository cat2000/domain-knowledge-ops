#!/usr/bin/env python3
"""
Write source-coverage.md from a descendants JSON + a classify(module).

Used by sync_domain_knowledge_from_confluence.py for any Confluence root; paths in the
markdown are relative to the output file (sibling ./pages/, ./descendants-full.json).

  python3 scripts/wiki/steps/source_coverage.py \\
    --json domain-knowledge/extracted/by-root/<根>/descendants-full.json \\
    --out domain-knowledge/extracted/by-root/<根>/source-coverage.md \\
    --classify-module scripts/facet_classify.py \\
    --root-page-id <根> \\
    --root-url 'https://...' \\
    --root-label 'Label'
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPTS = next(p for p in Path(__file__).resolve().parents if (p / "_install.py").is_file())
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
import _install

_install.bootstrap(__file__)

from wiki.steps.source_coverage_run import run_source_coverage


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate source-coverage.md from descendants JSON + classify()."
    )
    parser.add_argument("--json", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--classify-module", type=Path, required=True)
    parser.add_argument("--root-page-id", required=True)
    parser.add_argument("--root-url", required=True)
    parser.add_argument(
        "--root-label",
        default="",
        help="Anchor text for root link (default: Root <id>)",
    )
    parser.add_argument(
        "--pages-dir",
        type=Path,
        default=None,
        help="Optional: per-page <page_id>.md — title from front matter + body snippet for classify",
    )
    args = parser.parse_args()

    return run_source_coverage(
        json_path=args.json,
        out_path=args.out,
        classify_module=args.classify_module,
        root_page_id=args.root_page_id,
        root_url=args.root_url,
        root_label=args.root_label,
        pages_dir=args.pages_dir,
    )


if __name__ == "__main__":
    raise SystemExit(main())
