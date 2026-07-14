#!/usr/bin/env python3
"""Per-team Jira attribution config (proposition facets, Epic/title rules, normative slugs)."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping, Sequence

from jira.lib._paths import REPO_ROOT, SCRIPTS_DIR

TEAMS_DIR = REPO_ROOT / "domain-knowledge/jira/teams"


@lru_cache(maxsize=8)
def load_attribution_config(team_key: str | None = None, root_id: str | None = None) -> dict[str, Any] | None:
    if team_key:
        path = TEAMS_DIR / f"{team_key}.json"
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
    if root_id:
        for p in TEAMS_DIR.glob("*.json"):
            data = json.loads(p.read_text(encoding="utf-8"))
            if str(data.get("root_id")) == str(root_id):
                return data
    return None


def facets_tuple(cfg: dict[str, Any] | None) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Keyword facets from team.json only — pack has no default tenant facet table."""
    if not cfg:
        return ()
    out: list[tuple[str, tuple[str, ...]]] = []
    for row in cfg.get("facets") or []:
        if len(row) >= 2:
            out.append((str(row[0]), tuple(str(k) for k in row[1])))
    return tuple(out)


def sink_slugs(cfg: dict[str, Any] | None) -> frozenset[str]:
    if cfg:
        return frozenset(cfg.get("sink_slugs") or ["requirements", "gateway"])
    return frozenset({"requirements", "gateway"})


def normative_primaries(cfg: dict[str, Any] | None, root_id: str) -> frozenset[str]:
    """Confirmed slug = normative_business + distill_queue (business proposition, not scan dir)."""
    import sys

    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))
    from jira.lib.jira_checklist_themes import load_confirmed_themes

    slugs = set(load_confirmed_themes(root_id))
    try:
        from teams.registry import (
            jira_theme_for_proposition,
            legacy_scan_dir_for_proposition,
            team_key_for_root_id,
        )

        team_key = team_key_for_root_id(str(root_id))
        if team_key:
            for prop in list(slugs):
                jira = jira_theme_for_proposition(team_key, prop)
                if jira != prop:
                    slugs.add(jira)
            legacy = legacy_scan_dir_for_proposition(team_key)
            for prop in list(slugs):
                for legacy_dir, proposition in legacy.items():
                    if proposition == prop:
                        slugs.add(legacy_dir)
                if prop in legacy:
                    slugs.add(legacy[prop])
    except ImportError:
        pass
    if cfg:
        for s in cfg.get("normative_extra") or []:
            slugs.add(s)
    return frozenset(slugs)


def resolve_primary_hints(raw: Mapping[str, Any], cfg: dict[str, Any] | None) -> str | None:
    """Epic / 标题前缀 → primary（优先于关键词撞库）。"""
    if not cfg:
        return None
    summary = raw.get("summary") or ""
    parent_key = raw.get("parent_key")
    for epic_key, primary in (cfg.get("epic_primary") or {}).items():
        if parent_key == epic_key:
            return primary
    parent = raw.get("parent") or {}
    if isinstance(parent, dict):
        pk = parent.get("parent_key")
        for epic_key, primary in (cfg.get("epic_primary") or {}).items():
            if pk == epic_key or parent.get("key") == epic_key:
                return primary
        chain = raw.get("parent_chain") or []
        for node in chain:
            if isinstance(node, dict) and node.get("key") in (cfg.get("epic_primary") or {}):
                return cfg["epic_primary"][node["key"]]
    for rule in cfg.get("title_primary") or []:
        pat = rule.get("pattern")
        primary = rule.get("primary")
        if not pat or not primary:
            continue
        flags = re.I if rule.get("flags") == "i" else 0
        if re.search(pat, summary, flags):
            return primary
    return None
