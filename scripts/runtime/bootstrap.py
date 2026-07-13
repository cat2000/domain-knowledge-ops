"""Ensure ``scripts/`` is on ``sys.path``."""

from __future__ import annotations

import sys

from runtime.paths import SCRIPTS_DIR


def ensure_scripts_on_path() -> None:
    s = str(SCRIPTS_DIR)
    if s not in sys.path:
        sys.path.insert(0, s)
