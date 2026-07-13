"""Jira Agile board sprints: queue, cursor, cache (no CLI)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jira.lib.jira_sprints_http import fetch_board_sprints
from jira.lib.jira_team_config import (
    issuetype_jql_fragment,
    jira_base_dir,
    resolve_team,
)


def refresh_sprints_cli(team_arg: str, filter_origin_board: bool = False) -> None:
    from jira.lib._paths import REPO_ROOT
    from jira.lib.jira_team_config import atlassian_auth_header, load_dotenv

    load_dotenv()
    team_key, team = resolve_team(team_arg)
    auth = atlassian_auth_header()
    queue = build_sprint_queue(team, auth, filter_origin_board=filter_origin_board)
    path = save_sprint_cache(team_key, team, queue)
    print(f"jira_sprints: queue={len(queue)} → {path.relative_to(REPO_ROOT)}")


def resolve_sprint_for_fetch(
    team_key: str,
    team: dict[str, Any],
    state: dict[str, Any],
    auth: str,
    *,
    refresh: bool = False,
    sprint_id: int | None = None,
    filter_origin_board: bool = False,
) -> tuple[dict[str, Any], list[dict[str, Any]], int]:
    """
    Pick sprint for this run. Returns (sprint, full_queue, index).
    Advances ``state['sprint_cursor']`` only via ``advance_sprint_cursor`` after fetch.
    """
    root_id = str(team["root_id"])
    sprint_cursor = state.setdefault("sprint_cursor", {})

    if sprint_id is not None:
        queue = load_queue_from_cache(root_id) or build_sprint_queue(
            team, auth, filter_origin_board=filter_origin_board
        )
        for index, sprint in enumerate(queue):
            if int(sprint["id"]) == int(sprint_id):
                sprint_cursor["index"] = index
                sprint_cursor["total"] = len(queue)
                return sprint, queue, index
        raise SystemExit(f"Sprint id {sprint_id} not in queue for team {team_key}")

    if refresh or not load_queue_from_cache(root_id):
        queue = build_sprint_queue(team, auth, filter_origin_board=filter_origin_board)
        save_sprint_cache(team_key, team, queue)
    else:
        queue = load_queue_from_cache(root_id) or []

    if not queue:
        raise SystemExit(f"No sprints in queue for board {team['jira'].get('board_id')}")

    index = int(sprint_cursor.get("index") or 0)
    if index >= len(queue):
        sprint_cursor["completed"] = True
        raise SystemExit(
            f"Sprint queue complete ({len(queue)} sprints). Reset with --reset to re-run."
        )

    sprint = queue[index]
    sprint_cursor["total"] = len(queue)
    sprint_cursor["index"] = index
    sprint_cursor["current_sprint_id"] = sprint.get("id")
    sprint_cursor["current_sprint_name"] = sprint.get("name")
    sprint_cursor["completed"] = False
    return sprint, queue, index


def advance_sprint_cursor(state: dict[str, Any]) -> None:
    sprint_cursor = state.setdefault("sprint_cursor", {})
    index = int(sprint_cursor.get("index") or 0) + 1
    total = int(sprint_cursor.get("total") or 0)
    sprint_cursor["index"] = index
    sprint_cursor["last_completed_index"] = index - 1
    sprint_cursor["completed"] = index >= total


def build_sprint_jql(team: dict[str, Any], sprint_id: int) -> str:
    jira_cfg = team["jira"]
    parts = [
        jira_cfg["jql_base"],
        issuetype_jql_fragment(jira_cfg["issuetypes"]),
        f"sprint = {int(sprint_id)}",
    ]
    order = jira_cfg.get("sprint_issue_order", "key ASC")
    return " AND ".join(parts) + f" ORDER BY {order}"


def load_queue_from_cache(root_id: str) -> list[dict[str, Any]] | None:
    path = sprints_cache_path(root_id)
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    queue = data.get("sprints_iterate_queue")
    if queue:
        return queue
    closed = data.get("sprints") or data.get("sprints_closed") or []
    active = data.get("sprints_active") or []
    return list(closed) + list(active)


def save_sprint_cache(
    team_key: str,
    team: dict[str, Any],
    queue: list[dict[str, Any]],
    path: Path | None = None,
) -> Path:
    jira_cfg = team["jira"]
    path = path or sprints_cache_path(str(team["root_id"]))
    path.parent.mkdir(parents=True, exist_ok=True)
    closed = [s for s in queue if s.get("state") == "closed"]
    active = [s for s in queue if s.get("state") == "active"]
    payload = {
        "team": team_key,
        "board_id": jira_cfg.get("board_id"),
        "board_name": jira_cfg.get("board_name"),
        "sorted_by": "completeDate asc (closed); active appended",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "closed_count": len(closed),
        "active_count": len(active),
        "iterate_queue_count": len(queue),
        "sprints_closed": closed,
        "sprints_active": active,
        "sprints_iterate_queue": queue,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def sprints_cache_path(root_id: str) -> Path:
    return jira_base_dir(root_id) / "sprints-closed.json"


def build_sprint_queue(
    team: dict[str, Any],
    auth: str,
    *,
    filter_origin_board: bool = False,
) -> list[dict[str, Any]]:
    """Closed sprints (time asc) + active sprint(s) at end."""
    jira_cfg = team["jira"]
    board_id = int(jira_cfg["board_id"])
    closed = fetch_board_sprints(
        board_id, auth, state="closed", filter_origin_board=filter_origin_board
    )
    closed.sort(key=_sprint_sort_key)
    active = fetch_board_sprints(
        board_id, auth, state="active", filter_origin_board=filter_origin_board
    )
    active.sort(key=_sprint_sort_key)
    queue: list[dict[str, Any]] = []
    for sprint in closed:
        queue.append(_normalize_sprint(sprint, board_id, "closed"))
    for sprint in active:
        queue.append(_normalize_sprint(sprint, board_id, "active"))
    return queue


def _normalize_sprint(s: dict[str, Any], board_id: int, state: str) -> dict[str, Any]:
    return {
        "id": s.get("id"),
        "name": s.get("name"),
        "state": s.get("state") or state,
        "startDate": s.get("startDate"),
        "endDate": s.get("endDate"),
        "completeDate": s.get("completeDate"),
        "goal": s.get("goal"),
        "originBoardId": s.get("originBoardId"),
        "board_id": board_id,
    }


def _sprint_sort_key(s: dict[str, Any]) -> str:
    return s.get("completeDate") or s.get("endDate") or s.get("startDate") or ""
