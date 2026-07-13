"""Jira Classify attribution — run loop over raw/*.json."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from jira.steps.attribute_types import AttributeConfig
from jira.lib.attribute_logic import rebuild_index, result_to_yaml, should_preserve_attr
from jira.lib.jira_checklist_themes import load_allowed_themes
from jira.lib.jira_first_principles import classify_ticket
from jira.lib.jira_team_config import jira_base_dir, resolve_team


def run_attribute(config: AttributeConfig) -> int:
    team_key, team = resolve_team(config.team)
    root_id = str(team["root_id"])
    jira_dir = jira_base_dir(root_id)
    raw_dir = jira_dir / "raw"
    attr_dir = jira_dir / "attribution"
    attr_dir.mkdir(parents=True, exist_ok=True)

    raw_by_key: dict[str, dict] = {}
    for path in raw_dir.glob("*.json"):
        raw_by_key[path.stem] = json.loads(path.read_text(encoding="utf-8"))

    if config.keys:
        keys = [key.strip() for key in config.keys.split(",") if key.strip()]
    else:
        keys = sorted(raw_by_key.keys())

    scanned_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    written = skipped = 0

    for key in keys:
        raw = raw_by_key.get(key)
        if not raw:
            print(f"attribute_jira_tickets: skip missing raw/{key}.json", file=sys.stderr)
            continue
        attr_path = attr_dir / f"{key}.yaml"
        if config.preserve_cursor_reviewed and should_preserve_attr(attr_path):
            skipped += 1
            continue
        parent_raw = None
        parent_key = raw.get("parent_key")
        if parent_key and parent_key in raw_by_key:
            parent_raw = raw_by_key[parent_key]
        result = classify_ticket(
            raw,
            allowed_themes=load_allowed_themes(root_id),
            parent_raw=parent_raw,
            team_key=team_key,
            root_id=root_id,
        )
        attr_path.write_text(result_to_yaml(result, scanned_at), encoding="utf-8")
        written += 1

    index = rebuild_index(jira_dir, team_key, root_id)
    print(
        f"attribute_jira_tickets: team={team_key} wrote={written} skipped_preserve={skipped} "
        f"tickets_indexed={index['ticket_count']}"
    )
    print(f"  theme_hits: {index.get('theme_hits')}")
    print(f"  product_line_hits: {index.get('product_line_hits')}")
    return 0
