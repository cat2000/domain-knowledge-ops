"""CLI helpers and subprocess runner for sync pipeline."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from wiki.sync import pipeline_logic as pl
from runtime.paths import REPO_ROOT


def default_enum_mode() -> str:
    return pl.default_enum_mode(os.environ.get("CONFLUENCE_ENUM_MODE", ""))


def orchestrator_extract_workers(
    cli_workers: Optional[int], page_count: int
) -> Tuple[int, str]:
    return pl.orchestrator_extract_workers(
        cli_workers,
        page_count,
        os.environ.get("CONFLUENCE_EXTRACT_WORKERS", ""),
    )


def coerce_enum_page_size(cli_value: Optional[int]) -> int:
    return pl.coerce_enum_page_size(
        cli_value, os.environ.get("CONFLUENCE_ENUMERATE_PAGE_SIZE", "")
    )


def merge_page_ids(existing_csv: str, *extras: str) -> str:
    return pl.merge_page_ids(existing_csv, *extras)


def env_reuse_existing_by_root() -> bool:
    return pl.env_reuse_existing_by_root(
        os.environ.get("CONFLUENCE_REUSE_EXISTING_BY_ROOT", "")
    )


def run_cmd(cmd: list[str], env: Optional[dict] = None) -> None:
    print("+", " ".join(cmd), file=sys.stderr)
    subprocess.run(cmd, cwd=str(REPO_ROOT), check=True, env=env)
