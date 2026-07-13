#!/usr/bin/env python3
"""CLI wrapper for S6 reader-facing final draft quality checks."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPTS = next(p for p in Path(__file__).resolve().parents if (p / "_install.py").is_file())
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
import _install

_install.bootstrap(__file__)

from distill.s6_reader_quality_logic import run_s6_reader_quality  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="S6 reader-facing final draft quality checks.")
    parser.add_argument("--root-id", help="Only check this root page ID directory.")
    parser.add_argument("--warn-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = run_s6_reader_quality(root_id=args.root_id)

    if summary.issues:
        print("S6 reader quality issues:", file=sys.stderr)
        for issue in summary.issues:
            print(f"  {issue}", file=sys.stderr)
    if summary.warnings:
        print("S6 reader quality warnings:", file=sys.stderr)
        for warning in summary.warnings:
            print(f"  {warning}", file=sys.stderr)

    print(
        f"S6 reader quality check: checked_final_drafts={summary.checked} "
        f"issues={len(summary.issues)} warnings={len(summary.warnings)}"
    )
    if summary.issues and not args.warn_only:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
