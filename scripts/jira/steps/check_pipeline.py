#!/usr/bin/env python3
"""
Heuristic checks for Jira pipeline artifacts (no LLM).

  python3 scripts/jira/steps/check_pipeline.py --team cma --full-raw
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

from jira.steps.check_pipeline_run import run_check_pipeline
from jira.steps.check_pipeline_types import CheckPipelineConfig


def main() -> int:
    parser = argparse.ArgumentParser()
    from teams.registry import add_team_argument
    add_team_argument(parser, use_default=False)
    parser.add_argument("--root-id", help="Confluence root page id")
    parser.add_argument("--full-raw", action="store_true")
    args = parser.parse_args()

    if not args.team and not args.root_id:
        parser.error("Provide --team or --root-id")

    return run_check_pipeline(
        CheckPipelineConfig(
            team=args.team,
            root_id=args.root_id,
            full_raw=args.full_raw,
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
