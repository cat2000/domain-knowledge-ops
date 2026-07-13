"""Jira Ingest materialize — raw/*.json → materialized/<KEY>.md."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from jira.lib.jira_materialize_logic import raw_ticket_to_markdown
from jira.lib.jira_team_config import jira_base_dir, resolve_team
from jira.steps.materialize_types import JiraMaterializeConfig
from runtime.paths import REPO_ROOT


def run_jira_materialize(config: JiraMaterializeConfig) -> int:
    _, team = resolve_team(config.team)
    root_id = str(team["root_id"])
    jira_dir = jira_base_dir(root_id)
    raw_dir = jira_dir / "raw"
    out_dir = jira_dir / "materialized"
    if not raw_dir.is_dir():
        raise SystemExit(f"Missing raw dir: {raw_dir}")

    out_dir.mkdir(parents=True, exist_ok=True)
    written = 0
    for path in sorted(raw_dir.glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        key = str(doc.get("key") or path.stem)
        out_path = out_dir / f"{key}.md"
        out_path.write_text(raw_ticket_to_markdown(doc), encoding="utf-8")
        written += 1

    rel = out_dir.relative_to(REPO_ROOT)
    print(f"jira_materialize: wrote {written} files → {rel}", file=sys.stderr)
    return 0
