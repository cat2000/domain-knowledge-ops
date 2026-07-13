"""Shared paths for curated workspace gate scripts."""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = next(p for p in Path(__file__).resolve().parents if (p / "_install.py").is_file())
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
import _install

_install.bootstrap(__file__)

from runtime.domain_knowledge_paths import (  # noqa: E402
    CURATED_BY_ROOT,
    DOMAIN_KNOWLEDGE,
    MATERIALIZATION_CLOSURE_FILE,
    MATERIALIZED_BY_ROOT,
    NON_BUSINESS_HEADING,
    PASS_HEADINGS,
    resolve_closure_file,
)
from runtime.paths import REPO_ROOT, SCRIPTS_DIR  # noqa: E402

# Canonical names (SSOT: runtime.domain_knowledge_paths)
RULES_BY_ROOT = MATERIALIZED_BY_ROOT
DISTILLED_BY_ROOT = CURATED_BY_ROOT

PASS_HEADING = NON_BUSINESS_HEADING
PASS_MARKER = NON_BUSINESS_HEADING
SOURCE_CLOSURE_FILE = MATERIALIZATION_CLOSURE_FILE

__all__ = [
    "CURATED_BY_ROOT",
    "DISTILLED_BY_ROOT",
    "DOMAIN_KNOWLEDGE",
    "MATERIALIZATION_CLOSURE_FILE",
    "MATERIALIZED_BY_ROOT",
    "NON_BUSINESS_HEADING",
    "PASS_HEADING",
    "PASS_HEADINGS",
    "PASS_MARKER",
    "REPO_ROOT",
    "RULES_BY_ROOT",
    "SCRIPTS_DIR",
    "SOURCE_CLOSURE_FILE",
    "resolve_closure_file",
]
