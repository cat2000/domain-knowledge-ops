#!/usr/bin/env python3
"""
Classify · attribute (draft): first-principles attribution from jira/raw → attribution/*.yaml.

No LLM. Cursor refines edge cases (attribution_method: cursor_review).

  python3 scripts/jira/steps/attribute.py --team cma
  python3 scripts/jira/steps/attribute.py --team cma --keys DEV-1,DEV-2
  python3 scripts/jira/steps/attribute.py --team cma --no-preserve-cursor-reviewed
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

from jira.steps.attribute_run import run_attribute
from jira.steps.attribute_types import AttributeConfig


def main() -> int:
    parser = argparse.ArgumentParser()
    from teams.registry import add_team_argument
    add_team_argument(parser, required=True)
    parser.add_argument("--keys", help="Comma-separated KEY override")
    parser.add_argument(
        "--no-preserve-cursor-reviewed",
        action="store_true",
        help="Overwrite high-confidence / cursor_review YAML",
    )
    args = parser.parse_args()

    return run_attribute(
        AttributeConfig(
            team=args.team,
            keys=args.keys,
            preserve_cursor_reviewed=not args.no_preserve_cursor_reviewed,
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
