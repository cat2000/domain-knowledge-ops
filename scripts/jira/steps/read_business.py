#!/usr/bin/env python3
"""
Classify · read_business: theme index (遗漏扫描) from attributed tickets (no LLM).

  python3 scripts/jira/steps/read_business.py --team cma
  python3 scripts/jira/steps/read_business.py --team cma --theme checkout
  python3 scripts/jira/steps/read_business.py --team cma --confirmed-only

Default (prep): themes from _ticket_attribution.json (not checklist 确认).
After human 确认: re-run with --confirmed-only to refresh index for 确认 slugs only.
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

from jira.steps.read_business_run import run_read_business
from jira.steps.read_business_types import ReadBusinessConfig


def main() -> int:
    parser = argparse.ArgumentParser()
    from teams.registry import add_team_argument
    add_team_argument(parser)
    parser.add_argument("--theme", help="single theme slug")
    parser.add_argument(
        "--confirmed-only",
        action="store_true",
        help="only checklist 确认 slugs (after Recognize gate; not Classify prep default)",
    )
    args = parser.parse_args()

    return run_read_business(
        ReadBusinessConfig(
            team=args.team,
            theme=args.theme,
            confirmed_only=args.confirmed_only,
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
