"""Deliverable locale token map loader.

Provides locale-specific strings for deliverable labels, headings, and filenames.
English contracts cite token keys; agents emit locale-specific strings at runtime.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from runtime.paths import REPO_ROOT

_TOKEN_MAP_PATH = REPO_ROOT / "domain-knowledge" / "language" / "deliverable-locale-tokens.json"
_TEAM_ROOTS_PATH = REPO_ROOT / "domain-knowledge" / "jira" / "team-roots.json"
_FALLBACK_LOCALE = "en"


@lru_cache(maxsize=1)
def load_token_map() -> dict[str, Any]:
    """Load and cache the deliverable-locale-tokens.json file."""
    if not _TOKEN_MAP_PATH.is_file():
        return {"version": 1, "locales": {}}
    return json.loads(_TOKEN_MAP_PATH.read_text(encoding="utf-8"))


def default_locale() -> str:
    """Return team-roots.json defaults.deliverable_locale (fallback 'en')."""
    if not _TEAM_ROOTS_PATH.is_file():
        return _FALLBACK_LOCALE
    try:
        data = json.loads(_TEAM_ROOTS_PATH.read_text(encoding="utf-8"))
        locale = (data.get("defaults") or {}).get("deliverable_locale", _FALLBACK_LOCALE)
        return str(locale).strip() or _FALLBACK_LOCALE
    except (OSError, json.JSONDecodeError, AttributeError):
        return _FALLBACK_LOCALE


def locale_tokens(locale: str | None = None) -> dict[str, Any]:
    """Return the full token dict for the given locale (or default locale)."""
    resolved = locale if locale is not None else default_locale()
    locales = load_token_map().get("locales") or {}
    return dict(locales.get(resolved) or {})


def token(path: str, locale: str | None = None) -> str:
    """Resolve a dotted token path for a specific locale.

    Example: token("s5_headings.domain_model", "en") == "## Domain model"
    """
    resolved = locale if locale is not None else default_locale()
    locales = load_token_map().get("locales") or {}
    current: Any = locales.get(resolved) or {}
    for part in path.split("."):
        if not isinstance(current, dict):
            return ""
        current = current.get(part, "")
    return str(current) if current else ""


def all_locale_values(path: str) -> list[str]:
    """Return values for a token path from ALL locales (deduped, order: en first).

    Used by validators to accept any locale's strings.
    """
    locales = load_token_map().get("locales") or {}
    values: list[str] = []
    seen: set[str] = set()
    for locale_data in locales.values():
        current: Any = locale_data
        for part in path.split("."):
            if not isinstance(current, dict):
                current = ""
                break
            current = current.get(part, "")
        val = str(current).strip() if current else ""
        if val and val not in seen:
            seen.add(val)
            values.append(val)
    return values


def heading_matchers(path: str) -> list[str]:
    """Alias of all_locale_values; intended for heading-presence checks."""
    return all_locale_values(path)


def work_draft_globs() -> list[str]:
    """Return work-draft glob patterns for all locales."""
    return all_locale_values("filenames.work_draft_glob")


def locale_brief_globs() -> list[str]:
    """Return locale-brief (final draft) glob patterns for all locales."""
    return all_locale_values("filenames.locale_brief_glob")


def gap_scan_filename(locale: str | None = None) -> str:
    """Return the Classify gap-scan index filename for a locale (default: default_locale()).

    en -> gap-scan.md, zh-CN -> 遗漏扫描.md. Falls back to gap-scan.md if unresolved.
    """
    return token("filenames.gap_scan_filename", locale) or "gap-scan.md"


def full_key_index_filename(locale: str | None = None) -> str:
    """Return the Classify full-key-index filename for a locale (default: default_locale())."""
    return token("filenames.full_key_index_filename", locale) or "full-key-index.md"
