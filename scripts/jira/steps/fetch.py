#!/usr/bin/env python3
"""
Jira Ingest · fetch: issues into curated/by-root/<id>/jira/raw/.

Two strategies only:
  --mode sprint --sprint-id <id>   one sprint, all issues + comments
  --mode history                   next sprint in queue (closed → active)

Usage:
  python3 scripts/jira/steps/fetch.py --team cma --mode sprint --sprint-id 1726
  python3 scripts/jira/steps/fetch.py --team cma --mode history
  python3 scripts/jira/steps/fetch.py --team 150 --mode history
  python3 scripts/jira/lib/jira_sprints.py --team cma
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

from jira.steps.fetch_run import run_fetch_cli
from jira.steps.fetch_types import FetchConfig

# Re-exports for tests / legacy imports
from jira.lib.jira_fetch_http import (  # noqa: F401
    SEARCH_FIELDS,
    fetch_all_comments,
    fetch_issue_meta,
    http_json,
    normalize_issue,
    resolve_parent_record,
    search_issues,
)
from jira.lib.jira_fetch_logic import (  # noqa: F401
    adf_to_text,
    build_parent_index,
    field_text,
    load_sync_state,
    write_json,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Jira Ingest fetch → jira/raw/ (no LLM).")
    from teams.registry import add_team_argument
    add_team_argument(parser, required=True)
    parser.add_argument(
        "--mode",
        default="history",
        choices=("sprint", "history"),
        help="sprint = one --sprint-id; history = next sprint in closed→active queue",
    )
    parser.add_argument(
        "--sprint-id",
        type=int,
        help="Required for --mode sprint: fetch this sprint only",
    )
    parser.add_argument(
        "--refresh-sprints",
        action="store_true",
        help="Rebuild sprints-closed.json from board before fetch",
    )
    parser.add_argument(
        "--filter-origin-board",
        action="store_true",
        help="Sprint queue: only originBoardId == team board_id",
    )
    parser.add_argument(
        "--no-advance-sprint",
        action="store_true",
        help="Do not increment sprint_cursor after fetch (history mode only)",
    )
    parser.add_argument("--limit", type=int, help="Max issues this run")
    parser.add_argument(
        "--resolve-parent-chain",
        action="store_true",
        help="Walk fields.parent up to root (extra REST per ancestor)",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Clear sync-state sprint cursor before run",
    )
    parser.add_argument(
        "--no-handoff",
        action="store_true",
        help="Skip JIRA_PIPELINE_HANDOFF.json",
    )
    args = parser.parse_args()
    if args.mode == "sprint" and args.sprint_id is None:
        parser.error("--mode sprint requires --sprint-id")

    run_fetch_cli(
        FetchConfig(
            team=args.team,
            mode=args.mode,
            sprint_id=args.sprint_id,
            refresh_sprints=args.refresh_sprints,
            filter_origin_board=args.filter_origin_board,
            no_advance_sprint=args.no_advance_sprint,
            limit=args.limit,
            resolve_parent_chain=args.resolve_parent_chain,
            reset=args.reset,
            no_handoff=args.no_handoff,
        )
    )


if __name__ == "__main__":
    main()
