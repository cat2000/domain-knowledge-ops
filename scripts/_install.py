"""Locate ``scripts/`` from any nested module and activate ``_bootstrap`` (stdlib only)."""

from __future__ import annotations

import sys
from pathlib import Path


def bootstrap(caller: str) -> Path:
    """Insert ``scripts/`` on ``sys.path`` and import ``_bootstrap``."""
    scripts = next(
        p for p in Path(caller).resolve().parents if (p / "_bootstrap.py").is_file()
    )
    entry = str(scripts)
    if entry not in sys.path:
        sys.path.insert(0, entry)
    import _bootstrap  # noqa: F401

    from runtime.paths import SCRIPTS_DIR

    return SCRIPTS_DIR
