"""Declarative Jira pipeline steps (subprocess orchestration)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from jira.ingest_run import run_jira_ingest
from jira.ingest_types import JiraIngestConfig
from jira.lib.jira_team_config import resolve_team
from jira.run_types import JiraSyncConfig
from jira.steps.materialize_run import run_jira_materialize
from jira.steps.materialize_types import JiraMaterializeConfig


def run_jira_sync(
    config: JiraSyncConfig,
    *,
    repo: Path,
    scripts: Path,
    python: str | None = None,
) -> int:
    py = python or sys.executable

    def _run(cmd: list[str], label: str) -> None:
        run_cmd(cmd, label, repo=repo)

    team_key, team = resolve_team(config.team)
    root_id = str(team["root_id"])
    root = repo / "domain-knowledge" / "curated" / "by-root" / root_id
    ingest_mode = "sprint" if config.sprint_id is not None else "history"

    print("\n>>> Ingest: fetch", file=sys.stderr)
    run_jira_ingest(
        JiraIngestConfig(
            team=team_key,
            mode=ingest_mode,
            sprint_id=config.sprint_id,
            until_complete=config.sprint_id is None,
            force_fetch=config.fetch,
            skip_materialize=True,
        )
    )

    print("\n>>> Ingest: materialize (Recognize closure paths)", file=sys.stderr)
    run_jira_materialize(JiraMaterializeConfig(team=team_key))

    if not config.skip_attribute:
        _run(
            [py, str(scripts / "jira/steps/attribute.py"), "--team", team_key],
            "Classify: attribute (draft YAML)",
        )

    _run(
        [py, str(scripts / "jira/steps/read_business.py"), "--team", team_key],
        "Classify: business index (遗漏扫描)",
    )

    _domain_check(
        py,
        scripts,
        team_key,
        repo=repo,
        label="Classify gate: domain_check jira --full-raw",
        full_raw=True,
    )

    print("\n=== add-knowledge-from-jira: 备料 (Ingest+Classify) done — pause ===")
    print(f"root: {root}")
    print(
        "Cursor (RUNBOOK): Recognize — closure + DOMAIN_MODULE_CHECKLIST → 人标 确认 → "
        "unified Compose (S3–S6; Jira business evidence enters S3 through S2 closure/materialized)"
    )
    return 0


def _domain_check(
    py: str,
    scripts: Path,
    team: str,
    *,
    repo: Path,
    label: str,
    full_raw: bool = False,
) -> None:
    cmd = [py, str(scripts / "domain_check.py"), "jira", "--team", team]
    if full_raw:
        cmd.append("--full-raw")
    run_cmd(cmd, label, repo=repo)


def run_cmd(cmd: list[str], label: str, *, repo: Path) -> None:
    print(f"\n>>> {label}\n$ {' '.join(cmd)}", file=sys.stderr)
    result = subprocess.run(cmd, cwd=repo)
    if result.returncode != 0:
        raise SystemExit(f"{label} failed (exit {result.returncode})")
