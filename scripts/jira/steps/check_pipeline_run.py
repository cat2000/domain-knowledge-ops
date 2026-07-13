"""Jira pipeline artifact checks — orchestration and disk I/O."""

from __future__ import annotations

import json
from pathlib import Path

from jira.lib.attribution_yaml import parse_attribution_yaml_file
from jira.lib.jira_checklist_themes import load_allowed_themes
from jira.lib.jira_team_config import jira_base_dir, resolve_team
from jira.lib.pipeline_check_logic import (
    issues_for_attribution,
    issues_for_raw_ticket,
)
from jira.steps.check_pipeline_types import CheckPipelineConfig


def run_check_pipeline(config: CheckPipelineConfig) -> int:
    if config.team:
        _, team = resolve_team(config.team)
        root_id = str(team["root_id"])
    elif config.root_id:
        root_id = str(config.root_id).strip()
    else:
        raise ValueError("Provide team or root_id")

    jira_dir = jira_base_dir(root_id)
    issues: list[str] = []

    raw_dir = jira_dir / "raw"
    attr_dir = jira_dir / "attribution"
    manifest_keys: list[str] = []
    manifest_path = jira_dir / "batch-manifest.json"
    if manifest_path.is_file():
        manifest_keys = json.loads(manifest_path.read_text()).get("keys") or []

    keys = sorted(path.stem for path in raw_dir.glob("*.json")) if config.full_raw else manifest_keys
    if not keys and manifest_keys:
        keys = manifest_keys

    allowed = load_allowed_themes(root_id)

    for key in keys:
        raw_path = raw_dir / f"{key}.json"
        raw_exists = raw_path.is_file()
        doc = json.loads(raw_path.read_text(encoding="utf-8")) if raw_exists else None
        issues.extend(issues_for_raw_ticket(key, doc, raw_exists))

        attr_path = attr_dir / f"{key}.yaml"
        if not attr_path.is_file():
            issues.append(f"missing attribution/{key}.yaml (Classify attribute not run?)")
            continue
        meta = parse_attribution_yaml_file(attr_path)
        issues.extend(
            issues_for_attribution(
                key,
                meta,
                allowed=allowed,
            )
        )

    if keys and not (jira_dir / "_ticket_attribution.json").is_file():
        issues.append("missing _ticket_attribution.json")

    if issues:
        print(f"check_jira_pipeline: root={root_id} issues={len(issues)}")
        for issue in issues[:50]:
            print(f"  - {issue}")
        if len(issues) > 50:
            print(f"  ... and {len(issues) - 50} more")
        return 1

    print(f"check_jira_pipeline: root={root_id} ok (keys_checked={len(keys)})")
    return 0
