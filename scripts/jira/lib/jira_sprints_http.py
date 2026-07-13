"""Jira Agile REST helpers (board sprints)."""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Any


def agile_api_base() -> str:
    from runtime.atlassian_env import DEFAULT_ATLASSIAN_SITE

    base = os.environ.get("ATLASSIAN_BASE_URL", DEFAULT_ATLASSIAN_SITE).strip()
    base = base.rstrip("/")
    if base.endswith("/wiki"):
        base = base[: -len("/wiki")]
    return base + "/rest/agile/1.0"


def http_get_json(url: str, auth: str) -> Any:
    req = urllib.request.Request(
        url, headers={"Accept": "application/json", "Authorization": auth}
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode())


def fetch_board_sprints(
    board_id: int,
    auth: str,
    *,
    state: str,
    filter_origin_board: bool = False,
) -> list[dict[str, Any]]:
    """Paginate GET /board/{id}/sprint?state=..."""
    api = agile_api_base()
    out: list[dict[str, Any]] = []
    start_at = 0
    page = 50
    while True:
        url = (
            f"{api}/board/{board_id}/sprint?state={state}"
            f"&startAt={start_at}&maxResults={page}"
        )
        data = http_get_json(url, auth)
        values = data.get("values") or []
        for sprint in values:
            if filter_origin_board:
                origin_board = sprint.get("originBoardId")
                if origin_board is not None and int(origin_board) != int(board_id):
                    continue
            out.append(sprint)
        total = int(data.get("total") or 0)
        if start_at + len(values) >= total or not values:
            break
        start_at += len(values)
    return out
