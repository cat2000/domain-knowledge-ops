#!/usr/bin/env python3
"""
Jira Ingest: fetch (default); optional materialize with --materialize.

  python3 scripts/run_jira_ingest.py --team cma --mode sprint --sprint-id 1726
  python3 scripts/run_jira_ingest.py --team cma --mode history --until-complete --materialize
  python3 scripts/run_jira_ingest.py --team 150 --mode history --until-complete --materialize
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

from jira.ingest_run import run_jira_ingest
from jira.ingest_types import JiraIngestConfig


def main() -> int:
    parser = argparse.ArgumentParser(description="Jira Ingest: fetch (optional --materialize)")
    from teams.registry import add_team_argument
    add_team_argument(parser, required=True)
    parser.add_argument(
        "--mode",
        default="history",
        choices=("sprint", "history"),
        help="sprint: one --sprint-id; history: sprint queue",
    )
    parser.add_argument("--sprint-id", type=int, help="Required when --mode sprint")
    parser.add_argument(
        "--until-complete",
        action="store_true",
        help="history only: fetch every sprint until cursor completed",
    )
    parser.add_argument("--refresh-sprints", action="store_true")
    parser.add_argument("--filter-origin-board", action="store_true")
    parser.add_argument("--no-advance-sprint", action="store_true")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--resolve-parent-chain", action="store_true")
    parser.add_argument("--reset", action="store_true")
    parser.add_argument(
        "--fetch",
        action="store_true",
        help="history: fetch even when sprint_cursor.completed=true",
    )
    parser.add_argument(
        "--materialize",
        action="store_true",
        help="After fetch: raw/*.json → jira/materialized/*.md (default: fetch only)",
    )
    args = parser.parse_args()
    if args.mode == "sprint" and args.sprint_id is None:
        parser.error("--mode sprint requires --sprint-id")

    return run_jira_ingest(
        JiraIngestConfig(
            team=args.team,
            mode=args.mode,
            sprint_id=args.sprint_id,
            until_complete=args.until_complete,
            refresh_sprints=args.refresh_sprints,
            filter_origin_board=args.filter_origin_board,
            no_advance_sprint=args.no_advance_sprint,
            limit=args.limit,
            resolve_parent_chain=args.resolve_parent_chain,
            reset=args.reset,
            skip_materialize=not args.materialize,
            force_fetch=args.fetch,
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
