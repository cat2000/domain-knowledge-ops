"""Minimal YAML parsing for Jira attribution/*.yaml (no PyYAML)."""

from __future__ import annotations

from pathlib import Path


def parse_attribution_yaml(text: str) -> dict:
    record: dict = {}
    index = 0
    lines = text.splitlines()
    while index < len(lines):
        line = lines[index]
        if line.startswith("  - ") or ":" not in line:
            index += 1
            continue
        key, value = line.split(":", 1)
        key, value = key.strip(), value.strip()
        if value == "":
            items: list[str] = []
            index += 1
            while index < len(lines) and lines[index].startswith("  - "):
                items.append(lines[index][4:].strip())
                index += 1
            record[key] = items
            continue
        if value == "null":
            record[key] = None
        elif value == "true":
            record[key] = True
        elif value == "false":
            record[key] = False
        elif value == "[]":
            record[key] = []
        else:
            record[key] = value.strip('"')
        index += 1
    return record


def parse_attribution_yaml_file(path: Path) -> dict:
    return parse_attribution_yaml(path.read_text(encoding="utf-8"))
