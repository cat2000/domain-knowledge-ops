#!/usr/bin/env python3
"""
Aggregate per-page extracts into materialized/**/*.md by kb_outline (input `.md` use YAML front matter).
Output files are **Markdown only** (no front matter) — H1, source links, and body text.

Modes:
  --product mall|hui          Mall → by-root/48696506/pages；Hui → by-root/48694645/pages（各映射到对应 materialized/by-root）。
  --extracted-dir + --rules-base   Unified layout (任意 Confluence 根页 ID；通常由
                                   sync_domain_knowledge_from_confluence.py 传入)。

Skips pages with kb_outline \"—\". Overwrites target .md each run — Confluence
is canonical; fix source pages and re-sync.

  python3 scripts/wiki/steps/materialize.py --extracted-dir .../pages --rules-base .../materialized/by-root/123 --root-page-id 123
  python3 scripts/wiki/steps/materialize.py --product hui
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

from wiki.steps.materialize_run import materialize_dirs, run_materialize  # noqa: F401


def main() -> None:
    parser = argparse.ArgumentParser(description="Materialize materialized/*.md from extracted pages.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--product",
        choices=("hui", "mall"),
        help="Legacy: fixed extracted + rules paths",
    )
    group.add_argument(
        "--extracted-dir",
        type=Path,
        help="Directory of <page_id>.md extracts (e.g. .../by-root/<id>/pages)",
    )
    parser.add_argument(
        "--rules-base",
        type=Path,
        help="With --extracted-dir: rules output root (e.g. .../materialized/by-root/<id>)",
    )
    parser.add_argument(
        "--root-page-id",
        default="",
        help="Optional: log tag only (legacy unified CLI)",
    )
    run_materialize(parser.parse_args())


if __name__ == "__main__":
    main()
