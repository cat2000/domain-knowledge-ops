#!/usr/bin/env python3
"""
Jira pipeline orchestrator (aligned with Wiki 备料 / 成稿).

Default (备料): Ingest all sprints through current → Classify → domain_check --full-raw → pause.
--sprint-id: Ingest one sprint only, then Classify.
Recognize + unified Compose (S3–S6) = Cursor only (RUNBOOK).
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
from _bootstrap import REPO_ROOT, SCRIPTS_DIR

from jira.run_pipeline import run_jira_sync
from jira.run_types import JiraSyncConfig

SCRIPTS = SCRIPTS_DIR


def main() -> int:
    parser = argparse.ArgumentParser(description="Run add-knowledge-from-jira script pipeline")
    from teams.registry import add_team_argument
    add_team_argument(parser)
    parser.add_argument("--sprint-id", type=int, help="Fetch this sprint only, then Classify")
    parser.add_argument("--fetch", action="store_true", help="Fetch even when the history cursor is completed")
    parser.add_argument("--skip-attribute", action="store_true")
    args = parser.parse_args()

    return run_jira_sync(
        JiraSyncConfig(
            team=args.team,
            sprint_id=args.sprint_id,
            fetch=args.fetch,
            skip_attribute=args.skip_attribute,
        ),
        repo=REPO_ROOT,
        scripts=SCRIPTS_DIR,
    )


if __name__ == "__main__":
    sys.exit(main())
