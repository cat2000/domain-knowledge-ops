"""Repo paths and environment for Confluence sync."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from runtime.atlassian_env import load_dotenv as _load_dotenv
from runtime.paths import REPO_ROOT

FACET_CLASSIFY_MODULE = REPO_ROOT / "scripts/wiki/lib/facet_classify.py"


def load_dotenv() -> None:
    _load_dotenv()


def preferred_python() -> str:
    """Prefer repo ``.venv`` so optional KB deps (e.g. deep-translator) are importable."""
    for name in ("python3", "python"):
        p = REPO_ROOT / ".venv" / "bin" / name
        if p.is_file():
            return str(p)
    return sys.executable
