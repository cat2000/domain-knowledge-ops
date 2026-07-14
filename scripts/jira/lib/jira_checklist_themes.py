#!/usr/bin/env python3
"""Load theme slugs from DOMAIN_MODULE_CHECKLIST.md per team root."""

from __future__ import annotations

import sys
from pathlib import Path

from jira.lib._paths import REPO_ROOT, SCRIPTS_DIR

from runtime.checklist_modules import parse_checklist_rows  # noqa: E402
from runtime.domain_knowledge_paths import (  # noqa: E402
    CHECKLIST_STATUS_CONFIRMED,
    CHECKLIST_STATUS_PENDING,
    is_checklist_status_confirmed,
)

# Always allowed as attribution fallbacks (not confirmed-domain deliver targets).
FALLBACK_THEMES = frozenset({"gateway", "requirements", "facet-gateway", "facet-misc"})


def checklist_path(root_id: str) -> Path:
    return REPO_ROOT / "domain-knowledge/curated/by-root" / root_id / "DOMAIN_MODULE_CHECKLIST.md"


def _status_is_confirmed(status: str) -> bool:
    return is_checklist_status_confirmed(status)


def load_allowed_themes(root_id: str) -> frozenset[str]:
    path = checklist_path(root_id)
    if not path.is_file():
        # Fail closed: sinks only — never invent a tenant business theme set.
        return frozenset(FALLBACK_THEMES)
    rows = parse_checklist_rows(path.read_text(encoding="utf-8"))
    slugs = {slug for slug, _ in rows}
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))
    try:
        from teams.registry import jira_theme_names_for_team, team_key_for_root_id

        team_key = team_key_for_root_id(str(root_id))
        if team_key:
            slugs |= jira_theme_names_for_team(team_key)
    except ImportError:
        pass
    return frozenset(slugs | set(FALLBACK_THEMES))


def load_confirmed_themes(root_id: str) -> list[str]:
    """Slugs whose domain-module row is marked 确认 on the acceptance checklist."""
    path = checklist_path(root_id)
    if not path.is_file():
        return []
    out: list[str] = []
    for slug, status in parse_checklist_rows(path.read_text(encoding="utf-8")):
        if _status_is_confirmed(status):
            out.append(slug)
    return out


# Re-export for tests / callers that imported symbols from this module.
__all__ = [
    "FALLBACK_THEMES",
    "CHECKLIST_STATUS_CONFIRMED",
    "CHECKLIST_STATUS_PENDING",
    "checklist_path",
    "parse_checklist_rows",
    "load_allowed_themes",
    "load_confirmed_themes",
    "_status_is_confirmed",
]
