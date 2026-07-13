"""Jira Ingest orchestration: fetch → materialize."""

from __future__ import annotations

import sys
from pathlib import Path

from jira.ingest_types import JiraIngestConfig
from jira.lib.jira_team_config import jira_base_dir, resolve_team
from jira.steps.fetch_run import run_fetch, sprint_queue_completed
from jira.steps.fetch_types import FetchConfig
from jira.steps.materialize_run import run_jira_materialize
from jira.steps.materialize_types import JiraMaterializeConfig
from runtime.atlassian_env import load_dotenv
from runtime.paths import REPO_ROOT


def run_jira_ingest(config: JiraIngestConfig) -> int:
    load_dotenv()
    if config.mode == "sprint" and config.sprint_id is None:
        raise SystemExit("jira Ingest: --mode sprint requires --sprint-id")
    if config.until_complete and config.mode != "history":
        raise SystemExit("jira Ingest: --until-complete only applies to --mode history")

    fetch_config = FetchConfig(
        team=config.team,
        mode=config.mode,
        sprint_id=config.sprint_id,
        refresh_sprints=config.refresh_sprints,
        filter_origin_board=config.filter_origin_board,
        no_advance_sprint=config.no_advance_sprint,
        limit=config.limit,
        resolve_parent_chain=config.resolve_parent_chain,
        reset=config.reset,
    )

    _, team = resolve_team(config.team)
    root = jira_base_dir(str(team["root_id"]))

    if config.until_complete:
        max_rounds = 150
        force = config.force_fetch
        for round_num in range(1, max_rounds + 1):
            if sprint_queue_completed(root) and not force:
                print(
                    "jira Ingest: sprint queue already completed (skip fetch)",
                    file=sys.stderr,
                )
                break
            print(f"\n>>> jira Ingest fetch: history batch {round_num}", file=sys.stderr)
            run_fetch(fetch_config, repo_root=REPO_ROOT)
            fetch_config = FetchConfig(
                team=fetch_config.team,
                mode=fetch_config.mode,
                sprint_id=fetch_config.sprint_id,
                refresh_sprints=False,
                filter_origin_board=fetch_config.filter_origin_board,
                no_advance_sprint=fetch_config.no_advance_sprint,
                limit=fetch_config.limit,
                resolve_parent_chain=fetch_config.resolve_parent_chain,
                reset=False,
            )
            force = False
            if sprint_queue_completed(root):
                print("jira Ingest: sprint_cursor.completed=true", file=sys.stderr)
                break
        else:
            raise SystemExit(
                f"jira Ingest: exceeded {max_rounds} history batches without completed=true"
            )
    elif (
        config.mode == "history"
        and sprint_queue_completed(root)
        and not config.force_fetch
    ):
        print("jira Ingest: sprint queue completed (skip fetch)", file=sys.stderr)
    else:
        run_fetch(fetch_config, repo_root=REPO_ROOT)

    if not config.skip_materialize:
        print("\n>>> jira Ingest materialize", file=sys.stderr)
        return run_jira_materialize(JiraMaterializeConfig(team=config.team))

    return 0
