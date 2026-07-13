"""Types for Jira materialize step."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class JiraMaterializeConfig:
    team: str
