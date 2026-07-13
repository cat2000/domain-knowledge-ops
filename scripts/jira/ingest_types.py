"""Types for Jira Ingest (fetch + materialize)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

JiraIngestMode = Literal["sprint", "history"]


@dataclass(frozen=True)
class JiraIngestConfig:
    team: str
    mode: JiraIngestMode = "history"
    sprint_id: Optional[int] = None
    until_complete: bool = False
    refresh_sprints: bool = False
    filter_origin_board: bool = False
    no_advance_sprint: bool = False
    limit: Optional[int] = None
    resolve_parent_chain: bool = False
    reset: bool = False
    skip_materialize: bool = True
    force_fetch: bool = False
