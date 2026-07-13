"""Read business_extract tickets — orchestration and disk I/O."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from jira.lib.jira_checklist_themes import load_allowed_themes, load_confirmed_themes
from jira.lib.jira_team_config import jira_base_dir, resolve_team
from jira.lib.read_business_logic import scan_theme, themes_from_attribution
from jira.steps.read_business_types import ReadBusinessConfig
from runtime.deliverable_locale import default_locale, gap_scan_filename
from runtime.paths import REPO_ROOT


def load_raw_tickets(raw_dir: Path, keys: list[str]) -> dict[str, dict]:
    raw_by_key: dict[str, dict] = {}
    for path in raw_dir.glob("*.json"):
        key = path.stem
        if key in keys:
            raw_by_key[key] = json.loads(path.read_text(encoding="utf-8"))
    return raw_by_key


def resolve_read_business_themes(
    config: ReadBusinessConfig,
    *,
    root_id: str,
    tickets: dict[str, dict],
) -> list[str]:
    allowed = load_allowed_themes(root_id)
    if config.theme:
        return [config.theme]
    if config.confirmed_only:
        return [t for t in load_confirmed_themes(root_id) if t in allowed]
    return themes_from_attribution(tickets, allowed)


def run_read_business(config: ReadBusinessConfig) -> int:
    _, team = resolve_team(config.team)
    root_id = str(team["root_id"])
    jira_dir = jira_base_dir(root_id)
    raw_dir = jira_dir / "raw"
    attr_path = jira_dir / "_ticket_attribution.json"
    if not attr_path.is_file():
        raise SystemExit(
            "read_business: missing _ticket_attribution.json — run attribute.py first"
        )
    idx = json.loads(attr_path.read_text(encoding="utf-8"))["tickets"]
    parent_path = jira_dir / "_parent_index.json"
    parent_idx = (
        json.loads(parent_path.read_text(encoding="utf-8")).get("by_parent", {})
        if parent_path.is_file()
        else {}
    )
    allowed = load_allowed_themes(root_id)
    locale = default_locale()
    filename = gap_scan_filename(locale)

    themes = resolve_read_business_themes(config, root_id=root_id, tickets=idx)
    if not themes:
        scope = "confirmed" if config.confirmed_only else "attributed"
        print(f"read_business: no {scope} themes to scan (wrote nothing)", file=sys.stderr)
        return 0

    total = 0
    for theme in themes:
        if theme not in allowed:
            print(f"skip unknown theme {theme}", file=sys.stderr)
            continue
        keys = sorted(
            ticket_key
            for ticket_key, record in idx.items()
            if theme in (record.get("themes") or []) and record.get("business_extract")
        )
        total += len(keys)
        raw_by_key = load_raw_tickets(raw_dir, keys)
        out = jira_dir / "by-theme" / theme / filename
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            scan_theme(theme, keys, raw_by_key, parent_idx, idx, locale=locale),
            encoding="utf-8",
        )
        print(f"wrote {out.relative_to(REPO_ROOT)} ({len(keys)} tickets)")

    print(f"jira_read_business_tickets: read_text_total={total}")
    return 0
