"""Ensure ``scripts/`` is on ``sys.path``; expose SCRIPTS_DIR and REPO_ROOT."""

from __future__ import annotations

from runtime.bootstrap import ensure_scripts_on_path
from runtime.paths import REPO_ROOT, SCRIPTS_DIR

ensure_scripts_on_path()
