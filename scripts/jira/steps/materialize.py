#!/usr/bin/env python3
"""
Jira Ingest · materialize: faithful markdown from jira/raw/*.json.

  python3 scripts/jira/steps/materialize.py --team cma
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

from jira.steps.materialize_run import run_jira_materialize
from jira.steps.materialize_types import JiraMaterializeConfig


def main() -> int:
    parser = argparse.ArgumentParser(description="Materialize jira/raw → jira/materialized/")
    from teams.registry import add_team_argument
    add_team_argument(parser, required=True)
    args = parser.parse_args()
    return run_jira_materialize(JiraMaterializeConfig(team=args.team))


if __name__ == "__main__":
    raise SystemExit(main())
