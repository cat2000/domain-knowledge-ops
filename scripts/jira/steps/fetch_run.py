"""Jira fetch orchestration (idempotent extract; HTTP in jira_fetch_http)."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from jira.steps.fetch_types import FetchConfig
from jira.lib.jira_fetch_http import (
    SEARCH_FIELDS,
    http_json,
    normalize_issue,
    search_issues,
)
from jira.lib.jira_fetch_logic import (
    build_parent_index,
    build_pipeline_handoff,
    load_sync_state,
    write_json,
)
from jira.lib.jira_sprints_logic import (
    advance_sprint_cursor,
    build_sprint_jql,
    resolve_sprint_for_fetch,
)
from jira.lib.jira_team_config import jira_base_dir, resolve_team
from runtime.atlassian_env import JiraEnv, load_dotenv


def run_fetch_cli(config: FetchConfig) -> None:
    load_dotenv()
    from _bootstrap import REPO_ROOT

    run_fetch(config, repo_root=REPO_ROOT)


def run_fetch(config: FetchConfig, *, repo_root: Path) -> None:
    if config.mode == "sprint" and config.sprint_id is None:
        raise SystemExit("fetch: --mode sprint requires --sprint-id")

    team_key, team = resolve_team(config.team)
    root_id = str(team["root_id"])
    jira_dir = jira_base_dir(root_id)
    jira_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = jira_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    state_path = jira_dir / "sync-state.json"
    state = load_sync_state(state_path) if not config.reset else {}
    state.setdefault("team", team_key)
    state.setdefault("root_id", root_id)

    jira_cfg = team["jira"]
    filter_origin = config.filter_origin_board or bool(
        jira_cfg.get("sprint_filter_origin_board", False)
    )
    limit = config.limit or int(jira_cfg.get("sprint_issue_cap", 5000))

    jira = JiraEnv.from_env(required=True)
    assert jira is not None
    auth = jira.auth_header()
    api_base = jira.api_base_url

    no_advance = config.no_advance_sprint or config.mode == "sprint"
    current_sprint, sprint_queue, sprint_index = resolve_sprint_for_fetch(
        team_key,
        team,
        state,
        auth,
        refresh=config.refresh_sprints,
        sprint_id=config.sprint_id,
        filter_origin_board=filter_origin,
    )
    jql = build_sprint_jql(team, int(current_sprint["id"]))
    state["fetch_strategy"] = config.mode
    print(
        f"fetch_jira_tickets: {config.mode} "
        f"[{sprint_index + 1}/{len(sprint_queue)}] "
        f"id={current_sprint['id']} name={current_sprint.get('name')!r} "
        f"state={current_sprint.get('state')}",
        file=sys.stderr,
    )

    print(f"fetch_jira_tickets: team={team_key} root={root_id} mode={config.mode} cap={limit}")
    print(f"fetch_jira_tickets: JQL={jql}", file=sys.stderr)

    issues = search_issues(jql, auth, api_base, limit)

    fetched_keys: List[str] = []
    for issue in issues:
        key = issue.get("key")
        if not key:
            continue
        doc = normalize_issue(
            issue,
            auth,
            api_base,
            resolve_parent_chain=config.resolve_parent_chain,
        )
        write_json(raw_dir / f"{key}.json", doc)
        fetched_keys.append(key)

    state["last_fetch_at"] = datetime.now(timezone.utc).isoformat()
    state["last_sync_at"] = state["last_fetch_at"]
    state["mode"] = config.mode
    state["fetched_total"] = int(state.get("fetched_total") or 0) + len(fetched_keys)

    if not no_advance:
        advance_sprint_cursor(state)
        sprint_cursor = state.get("sprint_cursor") or {}
        if sprint_cursor.get("completed"):
            print(
                "fetch_jira_tickets: sprint queue complete (through active sprint).",
                file=sys.stderr,
            )

    write_json(state_path, state)
    manifest: Dict[str, Any] = {
        "team": team_key,
        "root_id": root_id,
        "mode": config.mode,
        "fetch_strategy": state.get("fetch_strategy"),
        "jql": jql,
        "keys": fetched_keys,
        "issue_cap": limit,
        "sprint": current_sprint,
        "sprint_index": sprint_index,
        "sprint_queue_total": len(sprint_queue) if sprint_queue else None,
        "sprint_cursor": state.get("sprint_cursor"),
    }
    write_json(jira_dir / "batch-manifest.json", manifest)

    parent_index = build_parent_index(raw_dir)
    parent_index["generated_at"] = datetime.now(timezone.utc).isoformat()
    write_json(jira_dir / "_parent_index.json", parent_index)

    if not config.no_handoff:
        handoff = build_pipeline_handoff(
            repo_root=repo_root,
            jira_dir=jira_dir,
            team_key=team_key,
            root_id=root_id,
            mode=config.mode,
            keys=fetched_keys,
            stage="s1",
        )
        handoff_path = jira_dir / "JIRA_PIPELINE_HANDOFF.json"
        write_json(handoff_path, handoff)
        print(f"fetch_jira_tickets: wrote {len(fetched_keys)} raw → {raw_dir}")
        print(f"fetch_jira_tickets: handoff → {handoff_path.relative_to(repo_root)}")
    else:
        print(f"fetch_jira_tickets: wrote {len(fetched_keys)} raw → {raw_dir}")

    if not fetched_keys:
        print(
            "fetch_jira_tickets: no issues returned (empty sprint result).",
            file=sys.stderr,
        )


def sprint_queue_completed(root: Path) -> bool:
    state_path = root / "sync-state.json"
    if not state_path.is_file():
        state_path = root / "jira" / "sync-state.json"
    if not state_path.is_file():
        return False
    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
        return bool(data.get("sprint_cursor", {}).get("completed"))
    except (json.JSONDecodeError, OSError):
        return False
