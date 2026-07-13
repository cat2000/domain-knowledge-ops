"""Types for Jira pipeline orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class JiraSyncConfig:
    team: str = ""
    sprint_id: Optional[int] = None
    fetch: bool = False
    skip_attribute: bool = False
