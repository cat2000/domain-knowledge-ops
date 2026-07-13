#!/usr/bin/env python3
"""Shared team config and paths for Jira KB pipeline (no LLM)."""

from __future__ import annotations

import json
import os
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from jira.lib._paths import REPO_ROOT
from runtime.atlassian_env import atlassian_auth_header, jira_api_base, load_dotenv

TEAM_ROOTS_PATH = REPO_ROOT / "domain-knowledge/jira/team-roots.json"


def load_team_roots() -> Dict[str, Any]:
    data = json.loads(TEAM_ROOTS_PATH.read_text(encoding="utf-8"))
    return data.get("teams") or {}


def _alias_index(teams: Dict[str, Any]) -> Dict[str, str]:
    """Map alias / legacy key → canonical team key from team-roots.json."""
    index: Dict[str, str] = {}
    for key, rec in teams.items():
        index[key.lower()] = key
        for alias in rec.get("aliases") or []:
            index[str(alias).strip().lower()] = key
    return index


def resolve_team(team_or_root: str) -> Tuple[str, Dict[str, Any]]:
    """Return (team_key, team_record).

    Accepts canonical team key, alias (e.g. legacy cma/bc/wc), root_id, or Jira board_id.
    """
    teams = load_team_roots()
    s = team_or_root.strip().lower()
    if s in teams:
        return s, teams[s]
    aliases = _alias_index(teams)
    if s in aliases:
        k = aliases[s]
        return k, teams[k]
    for key, rec in teams.items():
        if str(rec.get("root_id")) == s:
            return key, rec
        jira_cfg = rec.get("jira") or {}
        if str(jira_cfg.get("board_id")) == s:
            return key, rec
    known = ", ".join(sorted(teams)) or "(none)"
    raise SystemExit(
        f"Unknown team, root_id, or board_id: {team_or_root!r}. "
        f"Configured teams: {known}. Or pass a root_id / Jira board_id."
    )


def jira_base_dir(root_id: str) -> Path:
    return REPO_ROOT / "domain-knowledge/curated/by-root" / str(root_id) / "jira"


def smoke_keys_path(root_id: str) -> Path:
    return jira_base_dir(root_id) / "smoke-keys.json"


def quote_jql_string(s: str) -> str:
    if re.search(r'[\s"]', s):
        return '"' + s.replace('"', '\\"') + '"'
    return s


def issuetype_jql_fragment(types: List[str]) -> str:
    quoted = ", ".join(quote_jql_string(t) for t in types)
    return f"issuetype in ({quoted})"


def parse_window(window: str) -> Tuple[str, str]:
    """Parse YYYY-MM-DD..YYYY-MM-DD → (gte, lt)."""
    m = re.match(
        r"^(\d{4}-\d{2}-\d{2})\s*\.\.\s*(\d{4}-\d{2}-\d{2})$",
        window.strip(),
    )
    if not m:
        raise SystemExit(f"Invalid window format: {window!r}. Use YYYY-MM-DD..YYYY-MM-DD")
    return m.group(1), m.group(2)


def add_months(iso_date: str, months: int) -> str:
    y, m, d = (int(x) for x in iso_date.split("-"))
    m += months
    while m > 12:
        m -= 12
        y += 1
    while m < 1:
        m += 12
        y -= 1
    last_day = 28
    for day in (31, 30, 29, 28):
        try:
            date(y, m, day)
            last_day = day
            break
        except ValueError:
            continue
    d = min(d, last_day)
    return f"{y:04d}-{m:02d}-{d:02d}"


def default_window(team: Dict[str, Any], state: Optional[Dict[str, Any]]) -> Tuple[str, str]:
    jira_cfg = team["jira"]
    if state and state.get("window"):
        window_state = state["window"]
        return window_state["created_gte"], window_state["created_lt"]
    start = jira_cfg.get("default_start_date", "2018-01-01")
    months = int(jira_cfg.get("time_window_months", 3))
    end = add_months(start, months)
    return start, end


def parent_subtree_jql(parent_key: str, team: Optional[Dict[str, Any]] = None) -> str:
    """
    Jira hierarchy via ``fields.parent`` (JQL ``parent = <KEY>``).
    Includes the parent issue itself. Optional Epic Link fallback from team config.
    """
    key = parent_key.strip().upper()
    hmode = "parent"
    if team:
        hmode = (team.get("jira") or {}).get("hierarchy_filter", "parent")
    if hmode == "epic_link":
        return f'("Epic Link" = {key} OR key = {key})'
    if hmode == "both":
        return f'(parent = {key} OR "Epic Link" = {key} OR key = {key})'
    return f"(parent = {key} OR key = {key})"


def build_search_jql(
    team: Dict[str, Any],
    *,
    mode: str,
    window_gte: Optional[str] = None,
    window_lt: Optional[str] = None,
    cursor_created: Optional[str] = None,
    cursor_key: Optional[str] = None,
    last_sync_at: Optional[str] = None,
    epic_key: Optional[str] = None,
    keys: Optional[List[str]] = None,
) -> str:
    jira_cfg = team["jira"]
    parts = [jira_cfg["jql_base"], issuetype_jql_fragment(jira_cfg["issuetypes"])]

    if keys:
        quoted = ", ".join(keys)
        parts.append(f"key in ({quoted})")
    if epic_key:
        parts.append(parent_subtree_jql(epic_key, team))

    mode = mode.lower()
    if mode == "incremental" and last_sync_at:
        parts.append(f'updated >= "{last_sync_at}"')
    elif mode in ("batch", "full", "smoke") and not keys:
        if window_gte and window_lt:
            parts.append(f'created >= "{window_gte}"')
            parts.append(f'created < "{window_lt}"')
        if cursor_created and cursor_key:
            parts.append(
                f'(created > "{cursor_created}" OR (created = "{cursor_created}" AND key > {cursor_key}))'
            )
        elif cursor_created and not cursor_key:
            parts.append(f'created > "{cursor_created}"')

    order = jira_cfg.get("order", "created ASC, key ASC")
    return " AND ".join(parts) + f" ORDER BY {order}"


# Re-exported from runtime.atlassian_env (backward compat for jira callers).
