#!/usr/bin/env python3
"""Normalize team-roots.json v2/v3 into a flat-compatible in-memory shape.

See docs/TEAM_ROOTS_V3.md — one Confluence space = one library; teams mount libraries[].
Callers that expect team[\"root_id\"] keep working via primary-library flattening.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any


def _as_str(v: Any) -> str:
    return str(v).strip() if v is not None else ""


def _deliver_map(rec: dict[str, Any]) -> dict[str, Any]:
    raw = rec.get("deliver_by_proposition") or {}
    return dict(raw) if isinstance(raw, dict) else {}


def _team_library_keys(team: dict[str, Any]) -> list[str]:
    if isinstance(team.get("libraries"), list) and team["libraries"]:
        return [_as_str(x) for x in team["libraries"] if _as_str(x)]
    single = _as_str(team.get("library"))
    if single:
        return [single]
    return []


def expand_v2_to_v3(raw: dict[str, Any]) -> dict[str, Any]:
    """If file has no libraries{}, treat each team as its own single-source library."""
    out = copy.deepcopy(raw)
    teams = dict(out.get("teams") or {})
    libraries = dict(out.get("libraries") or {})
    if libraries:
        out["version"] = int(out.get("version") or 3)
        return out

    for key, rec in teams.items():
        if not isinstance(rec, dict):
            continue
        root_id = _as_str(rec.get("root_id"))
        libraries[key] = {
            "display_name": rec.get("display_name") or key,
            "library_id": root_id or key,
            "root_id": root_id,
            "confluence_overview": rec.get("confluence_overview"),
            "space_key": rec.get("space_key"),
            "s2_profile": rec.get("s2_profile") or "default",
            "deliver_by_proposition": _deliver_map(rec),
        }
        # Keep team fields; mark mount
        rec = dict(rec)
        rec["libraries"] = [key]
        teams[key] = rec

    out["libraries"] = libraries
    out["teams"] = teams
    out["version"] = 3
    return out


def flatten_teams_for_compat(doc: dict[str, Any]) -> dict[str, Any]:
    """Attach primary-library root_id / deliver map onto each team for v2 callers."""
    out = copy.deepcopy(doc)
    libraries = dict(out.get("libraries") or {})
    teams = dict(out.get("teams") or {})

    for key, rec in list(teams.items()):
        if not isinstance(rec, dict):
            continue
        lib_keys = _team_library_keys(rec)
        if not lib_keys:
            # Legacy team with inline root_id only
            lib_keys = [key] if key in libraries else []
        primary_key = lib_keys[0] if lib_keys else ""
        primary = dict(libraries.get(primary_key) or {})

        flat = dict(rec)
        flat["libraries"] = lib_keys or flat.get("libraries") or []
        if primary:
            if not flat.get("root_id"):
                flat["root_id"] = primary.get("root_id") or primary.get("library_id")
            if not flat.get("confluence_overview"):
                flat["confluence_overview"] = primary.get("confluence_overview")
            if not flat.get("s2_profile"):
                flat["s2_profile"] = primary.get("s2_profile") or "default"
            # Merge deliver maps: earlier libraries win on key collision
            merged: dict[str, Any] = {}
            for lk in reversed(lib_keys):
                merged.update(_deliver_map(libraries.get(lk) or {}))
            if flat.get("deliver_by_proposition"):
                # Explicit team-level map wins
                merged.update(_deliver_map(flat))
            elif merged:
                flat["deliver_by_proposition"] = merged
            elif primary.get("deliver_by_proposition"):
                flat["deliver_by_proposition"] = _deliver_map(primary)
        teams[key] = flat

    out["teams"] = teams
    out["libraries"] = libraries
    return out


def normalize_team_roots_doc(raw: dict[str, Any]) -> dict[str, Any]:
    return flatten_teams_for_compat(expand_v2_to_v3(raw))


def load_normalized_team_roots(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    # Strip non-JSON helper keys sometimes present in examples
    if isinstance(raw, dict):
        raw = {k: v for k, v in raw.items() if not str(k).startswith("_")}
    return normalize_team_roots_doc(raw)


def libraries_for_team(doc: dict[str, Any], team_key: str) -> list[str]:
    teams = doc.get("teams") or {}
    rec = teams.get(team_key) or {}
    return list(rec.get("libraries") or _team_library_keys(rec))


def library_record(doc: dict[str, Any], library_key: str) -> dict[str, Any] | None:
    libs = doc.get("libraries") or {}
    rec = libs.get(library_key)
    return dict(rec) if isinstance(rec, dict) else None


def library_key_for_root_id(doc: dict[str, Any], root_id: str) -> str | None:
    rid = _as_str(root_id)
    for key, rec in (doc.get("libraries") or {}).items():
        if not isinstance(rec, dict):
            continue
        if _as_str(rec.get("root_id")) == rid or _as_str(rec.get("library_id")) == rid:
            return str(key)
    # v2-compat: team inline root
    for key, rec in (doc.get("teams") or {}).items():
        if isinstance(rec, dict) and _as_str(rec.get("root_id")) == rid:
            return str(key)
    return None


def team_keys_for_library(doc: dict[str, Any], library_key: str) -> list[str]:
    out: list[str] = []
    for key, rec in (doc.get("teams") or {}).items():
        if not isinstance(rec, dict):
            continue
        if library_key in (rec.get("libraries") or _team_library_keys(rec)):
            out.append(str(key))
    return sorted(out)
