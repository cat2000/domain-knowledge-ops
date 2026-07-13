"""Configuration for Jira Classify attribution."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AttributeConfig:
    team: str
    keys: str | None = None
    preserve_cursor_reviewed: bool = True
