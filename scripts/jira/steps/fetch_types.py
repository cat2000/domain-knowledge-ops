"""Types for Jira Ingest fetch orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

FetchMode = Literal["sprint", "history"]


@dataclass
class FetchConfig:
    team: str
    mode: FetchMode = "history"
    sprint_id: Optional[int] = None
    refresh_sprints: bool = False
    filter_origin_board: bool = False
    no_advance_sprint: bool = False
    limit: Optional[int] = None
    resolve_parent_chain: bool = False
    reset: bool = False
    no_handoff: bool = False
