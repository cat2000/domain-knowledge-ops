#!/usr/bin/env python3
"""Team SSOT: domain-knowledge/jira/team-roots.json (v2 or v3; see docs/TEAM_ROOTS_V3.md)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jira.lib.jira_team_config import (
    clear_team_roots_cache,
    load_libraries as _load_libraries,
    load_team_roots as _load_teams,
    resolve_team as _resolve_team,
)
from runtime.paths import REPO_ROOT
from teams.team_roots_normalize import (
    libraries_for_team as _libraries_for_team_doc,
    library_key_for_root_id as _library_key_for_root_id,
    library_record as _library_record,
    load_normalized_team_roots,
    team_keys_for_library as _team_keys_for_library,
)

TEAM_ROOTS_PATH = REPO_ROOT / "domain-knowledge/jira/team-roots.json"

_ROOT_TO_TEAM: dict[str, str] | None = None
_DOC: dict[str, Any] | None = None


def _doc() -> dict[str, Any]:
    global _DOC
    if _DOC is None:
        _DOC = load_normalized_team_roots(TEAM_ROOTS_PATH)
    return _DOC


def clear_caches() -> None:
    global _DOC, _ROOT_TO_TEAM
    _DOC = None
    _ROOT_TO_TEAM = None
    clear_team_roots_cache()


def load_team_roots() -> dict[str, Any]:
    return dict(_load_teams())


def load_libraries() -> dict[str, Any]:
    return dict(_load_libraries())


def load_defaults() -> dict[str, Any]:
    return dict(_doc().get("defaults") or {})


def configured_team_keys() -> list[str]:
    """Canonical team keys from team-roots.json (any N ≥ 1)."""
    return sorted(load_team_roots())


def default_team_key() -> str | None:
    """Optional default team: defaults.default_team, else sole team, else None."""
    teams = load_team_roots()
    if not teams:
        return None
    preferred = str(load_defaults().get("default_team") or "").strip()
    if preferred:
        if preferred in teams:
            return preferred
        try:
            key, _ = resolve_team(preferred)
            return key
        except SystemExit:
            return None
    if len(teams) == 1:
        return next(iter(teams))
    return None


def resolve_team(team_or_root: str) -> tuple[str, dict[str, Any]]:
    return _resolve_team(team_or_root)


def add_team_argument(
    parser: Any,
    *,
    required: bool = False,
    use_default: bool = True,
    help_suffix: str = "",
) -> None:
    """Add ``--team`` that accepts any configured key / alias / root_id / board_id."""
    keys = configured_team_keys()
    key_hint = "|".join(keys) if keys else "<team-key>"
    help_text = (
        f"Team key from team-roots.json ({key_hint}), or root_id / Jira board_id"
        f"{help_suffix}"
    )
    kwargs: dict[str, Any] = {"help": help_text}
    if required:
        kwargs["required"] = True
    elif use_default:
        default = default_team_key()
        if default is not None:
            kwargs["default"] = default
        else:
            kwargs["default"] = None
    else:
        kwargs["default"] = None
    parser.add_argument("--team", **kwargs)


def libraries_for_team(team_key: str) -> list[str]:
    return _libraries_for_team_doc(_doc(), team_key)


def library_for_root_id(root_id: str) -> dict[str, Any] | None:
    key = _library_key_for_root_id(_doc(), root_id)
    if not key:
        return None
    return _library_record(_doc(), key)


def team_key_for_root_id(root_id: str) -> str | None:
    """First team that mounts the library for this root (stable sort)."""
    global _ROOT_TO_TEAM
    if _ROOT_TO_TEAM is None:
        _ROOT_TO_TEAM = {}
        doc = _doc()
        for lib_key, lib in (doc.get("libraries") or {}).items():
            if not isinstance(lib, dict):
                continue
            rid = str(lib.get("root_id") or lib.get("library_id") or "")
            if not rid:
                continue
            teams = _team_keys_for_library(doc, str(lib_key))
            if teams:
                _ROOT_TO_TEAM[rid] = teams[0]
        # v2 inline
        for tkey, rec in (doc.get("teams") or {}).items():
            if isinstance(rec, dict) and rec.get("root_id"):
                _ROOT_TO_TEAM.setdefault(str(rec["root_id"]), str(tkey))
    return _ROOT_TO_TEAM.get(str(root_id))


def team_record_for_root_id(root_id: str) -> dict[str, Any] | None:
    key = team_key_for_root_id(root_id)
    if not key:
        return None
    return load_team_roots().get(key)


def _deliver_map_from_record(rec: dict[str, Any]) -> dict[str, tuple[str, str]]:
    raw = rec.get("deliver_by_proposition") or {}
    out: dict[str, tuple[str, str]] = {}
    for slug, pair in raw.items():
        if isinstance(pair, (list, tuple)) and len(pair) >= 2:
            out[str(slug)] = (str(pair[0]), str(pair[1]))
    return out


def deliver_by_proposition(team_key: str) -> dict[str, tuple[str, str]]:
    rec = load_team_roots().get(team_key) or {}
    return _deliver_map_from_record(rec)


def jira_theme_for_proposition(team_key: str, proposition_slug: str) -> str:
    rec = load_team_roots().get(team_key) or {}
    theme_map = rec.get("jira_theme_for_proposition") or {}
    return str(theme_map.get(proposition_slug, proposition_slug))


def jira_theme_to_proposition_slug(team_key: str, theme: str) -> str:
    """Map Jira Classify ``primary`` / ``themes[]`` slug to checklist proposition slug."""
    slug = str(theme or "").strip()
    if not slug:
        return slug
    rec = load_team_roots().get(team_key) or {}
    theme_map = rec.get("jira_theme_for_proposition") or {}
    inverse = {str(v): str(k) for k, v in theme_map.items()}
    if slug in inverse:
        return inverse[slug]
    legacy = rec.get("legacy_scan_dir_for_proposition") or {}
    if slug in legacy:
        return str(legacy[slug])
    if slug in (rec.get("deliver_by_proposition") or {}):
        return slug
    return slug


def legacy_scan_dir_for_proposition(team_key: str) -> dict[str, str]:
    """Legacy Jira by-theme dir name → proposition slug (optional)."""
    rec = load_team_roots().get(team_key) or {}
    raw = rec.get("legacy_scan_dir_for_proposition") or {}
    return {str(k): str(v) for k, v in raw.items()}


def jira_theme_names_for_team(team_key: str) -> set[str]:
    """Theme directory names that Classify may emit for this team."""
    rec = load_team_roots().get(team_key) or {}
    names: set[str] = set()
    theme_map = rec.get("jira_theme_for_proposition") or {}
    names.update(str(v) for v in theme_map.values())
    names.update(legacy_scan_dir_for_proposition(team_key).keys())
    names.update(deliver_by_proposition(team_key).keys())
    return names


def default_proposition_slugs(team_or_root: str) -> list[str]:
    key, _ = resolve_team(team_or_root)
    return list(deliver_by_proposition(key))


def resolve_deliver_path(
    root: Path, team_or_root: str, proposition_or_theme: str
) -> tuple[Path | None, str]:
    """Return (deliver_md path, jira by-theme directory name).

    Filename resolution is locale-aware: prefers the map entry, then the active
    ``deliverable_locale`` S7 suffix, then any known locale brief on disk.
    """
    from runtime.deliverable_locale import resolve_locale_brief_path

    team_key, _team_rec = resolve_team(team_or_root)
    deliver_map = deliver_by_proposition(team_key)

    prop = proposition_or_theme
    pair = deliver_map.get(prop)
    if not pair:
        prop = jira_theme_to_proposition_slug(team_key, proposition_or_theme)
        pair = deliver_map.get(prop)
    if not pair:
        return None, proposition_or_theme

    d, fname = pair
    deliver_dir = root / "_deliver" / d
    resolved = resolve_locale_brief_path(deliver_dir, prop, fname)
    if resolved is not None:
        return resolved, jira_theme_for_proposition(team_key, prop)
    # Map entry path even if missing (callers may want to create it)
    return deliver_dir / fname, jira_theme_for_proposition(team_key, prop)
