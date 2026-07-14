"""Shared S1/S2 profile loader from domain-knowledge/s2-domain-profiles.json."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from runtime.domain_knowledge_paths import DOMAIN_KNOWLEDGE


PROFILE_PATH = DOMAIN_KNOWLEDGE / "s2-domain-profiles.json"
TEAM_ROOTS_PATH = DOMAIN_KNOWLEDGE / "jira/team-roots.json"


def _compile_union(tokens: list[str]) -> re.Pattern[str]:
    parts = [t.strip() for t in tokens if str(t).strip()]
    body = "|".join(parts) if parts else r"$^"
    return re.compile(rf"({body})", re.IGNORECASE)


@lru_cache(maxsize=1)
def load_domain_profiles() -> dict:
    raw = json.loads(PROFILE_PATH.read_text(encoding="utf-8", errors="replace"))
    if not isinstance(raw, dict):
        raise ValueError(f"invalid profile root: {PROFILE_PATH}")
    return raw


def _load_normalized_team_roots_doc() -> dict:
    if not TEAM_ROOTS_PATH.is_file():
        return {}
    try:
        from teams.team_roots_normalize import load_normalized_team_roots

        doc = load_normalized_team_roots(TEAM_ROOTS_PATH)
        return doc if isinstance(doc, dict) else {}
    except (ImportError, OSError, ValueError, json.JSONDecodeError, TypeError, KeyError):
        raw = json.loads(TEAM_ROOTS_PATH.read_text(encoding="utf-8", errors="replace"))
        return raw if isinstance(raw, dict) else {}


@lru_cache(maxsize=1)
def load_team_roots() -> dict:
    """Return teams with primary-library fields flattened (v3-compatible)."""
    return dict(_load_normalized_team_roots_doc().get("teams") or {})


def _library_root_ids() -> dict[str, str]:
    """library_key → root_id from team-roots (v3 libraries{} or flattened)."""
    doc = _load_normalized_team_roots_doc()
    out: dict[str, str] = {}
    for key, rec in (doc.get("libraries") or {}).items():
        if not isinstance(rec, dict):
            continue
        rid = str(rec.get("root_id") or rec.get("library_id") or "").strip()
        if rid:
            out[str(key)] = rid
    return out


def team_key_for_scope(scope: str | None) -> str | None:
    if not scope:
        return None
    raw = load_domain_profiles()
    profiles_by_team = raw.get("profiles_by_team") or {}
    value = str(scope).strip()
    if value in profiles_by_team:
        return value
    for key, rec in load_team_roots().items():
        if str(rec.get("root_id") or "").strip() == value:
            return str(key)
    # Match library root_id → first team that mounts it (v3)
    for lib_key, rid in _library_root_ids().items():
        if rid != value:
            continue
        for team_key, rec in load_team_roots().items():
            libs = rec.get("libraries") if isinstance(rec, dict) else None
            if isinstance(libs, list) and lib_key in [str(x) for x in libs]:
                return str(team_key)
            if team_key == lib_key:
                return str(team_key)
    return None


def _team_record_for_scope(scope: str | None) -> tuple[str | None, dict | None]:
    if not scope:
        return None, None
    value = str(scope).strip()
    teams = load_team_roots()
    if value in teams:
        return value, teams[value]
    for key, rec in teams.items():
        if str(rec.get("root_id") or "").strip() == value:
            return str(key), rec
    team_key = team_key_for_scope(value)
    if team_key and team_key in teams:
        return team_key, teams[team_key]
    return None, None


def _profile_for_scope(scope: str | None) -> dict:
    raw = load_domain_profiles()
    value = str(scope).strip() if scope else ""
    if not value:
        return raw
    profiles_by_team = raw.get("profiles_by_team") or {}
    team_key, team_rec = _team_record_for_scope(value)
    if not team_key and value in profiles_by_team:
        team_key = value
    if not team_key:
        raise ValueError(
            f"unknown S2 profile scope: {value}. Add the root to {TEAM_ROOTS_PATH} "
            f"and configure profiles_by_team.<team> in {PROFILE_PATH}."
        )
    scoped = profiles_by_team.get(team_key)
    if not scoped:
        if str((team_rec or {}).get("s2_profile") or "").strip() == "default":
            return raw
        raise ValueError(
            f"missing S2 domain profile for team '{team_key}' (scope={value}). "
            f"Configure profiles_by_team.{team_key} in {PROFILE_PATH}, or explicitly "
            f"set s2_profile='default' in {TEAM_ROOTS_PATH} only when the default "
            f"profile is intentionally correct for this team."
        )
    merged = dict(raw)
    merged.update(scoped)
    if "s2" in scoped:
        merged["s2"] = {**(raw.get("s2") or {}), **(scoped.get("s2") or {})}
    return merged


def load_checklist_themes(scope: str | None = None) -> list[tuple[str, str, str]]:
    raw = _profile_for_scope(scope)
    out: list[tuple[str, str, str]] = []
    for row in raw.get("checklist_themes") or []:
        slug = str(row.get("slug") or "").strip()
        name_cn = str(row.get("name_cn") or "").strip()
        axis = str(row.get("axis") or "").strip()
        if slug and name_cn and axis:
            out.append((slug, name_cn, axis))
    return out


EMPTY_THEMES_HINT = (
    "checklist_themes is empty. Fill domain-knowledge/strategy.md §2 via @setup-domain-ops, "
    "derive s2-domain-profiles.json, and confirm themes before S1/S2. "
    f"See {PROFILE_PATH}."
)


def require_checklist_themes(scope: str | None = None) -> list[tuple[str, str, str]]:
    """Load themes or raise — open-source shell ships empty until strategy-derived."""
    themes = load_checklist_themes(scope)
    if not themes:
        raise ValueError(EMPTY_THEMES_HINT)
    return themes


def load_s1_facet_rules() -> tuple[tuple[str, str, tuple[str, ...]], ...]:
    raw = load_domain_profiles()
    rows = raw.get("s1_facets") or []
    out: list[tuple[str, str, tuple[str, ...]]] = []
    for row in rows:
        facet_dir = str(row.get("facet_dir") or "").strip()
        theme_label = str(row.get("theme_label") or "").strip()
        keywords = tuple(str(x).strip() for x in (row.get("keywords") or []) if str(x).strip())
        if facet_dir and theme_label and keywords:
            out.append((facet_dir, theme_label, keywords))
    return tuple(out)


def load_s1_noise_rules() -> dict[str, object]:
    raw = load_domain_profiles()
    cfg = raw.get("s1_noise") or {}
    return {
        "min_title_chars": int(cfg.get("min_title_chars") or 2),
        "exact_titles": tuple(str(x).strip() for x in (cfg.get("exact_titles") or []) if str(x).strip()),
        "title_prefixes": tuple(str(x).strip() for x in (cfg.get("title_prefixes") or []) if str(x).strip()),
    }


def load_s2_profiles(scope: str | None = None) -> dict:
    raw = _profile_for_scope(scope)
    s2 = raw.get("s2") or {}
    domain_cues_raw = s2.get("domain_cues") or {}
    domain_cues = {
        str(slug).strip(): _compile_union([str(x) for x in cues])
        for slug, cues in domain_cues_raw.items()
        if str(slug).strip()
    }
    route_overrides: list[tuple[re.Pattern[str], str, str]] = []
    for row in s2.get("route_overrides") or []:
        pat = str(row.get("pattern") or "").strip()
        slug = str(row.get("slug") or "").strip()
        reason = str(row.get("reason") or "").strip()
        if pat and slug:
            route_overrides.append((re.compile(pat, re.IGNORECASE), slug, reason))

    return {
        "primary_facet_to_slug": {
            str(k).strip(): str(v).strip()
            for k, v in (s2.get("primary_facet_to_slug") or {}).items()
            if str(k).strip() and str(v).strip()
        },
        "domain_cues": domain_cues,
        "business_signal_re": _compile_union([str(x) for x in (s2.get("business_signals") or [])]),
        "strong_cue_re": _compile_union([str(x) for x in (s2.get("strong_cues") or [])]),
        "engineering_noise_re": _compile_union([str(x) for x in (s2.get("engineering_noise") or [])]),
        "hard_non_business_path_re": _compile_union([str(x) for x in (s2.get("hard_non_business_path") or [])]),
        "explicit_non_business_path_re": _compile_union([str(x) for x in (s2.get("explicit_non_business_path") or [])]),
        "route_overrides": route_overrides,
    }


__all__ = [
    "EMPTY_THEMES_HINT",
    "PROFILE_PATH",
    "load_checklist_themes",
    "load_domain_profiles",
    "load_s1_facet_rules",
    "load_s1_noise_rules",
    "load_s2_profiles",
    "load_team_roots",
    "require_checklist_themes",
    "team_key_for_scope",
]
