#!/usr/bin/env python3
"""Jira Agile board sprints: list, sort, queue cursor (no LLM)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPTS = next(p for p in Path(__file__).resolve().parents if (p / "_install.py").is_file())
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
import _install

_install.bootstrap(__file__)

from jira.lib.jira_sprints_logic import refresh_sprints_cli

# Backward-compatible re-exports for fetch_run and tests.
from jira.lib.jira_sprints_logic import (  # noqa: F401
    advance_sprint_cursor,
    build_sprint_jql,
    build_sprint_queue,
    load_queue_from_cache,
    resolve_sprint_for_fetch,
    save_sprint_cache,
    sprints_cache_path,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh sprint queue JSON for a team board.")
    parser.add_argument("--team", required=True)
    parser.add_argument(
        "--filter-origin-board",
        action="store_true",
        help="Only sprints where originBoardId matches board_id",
    )
    args = parser.parse_args()
    refresh_sprints_cli(args.team, filter_origin_board=args.filter_origin_board)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
