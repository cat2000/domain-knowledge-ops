"""Types for check_pipeline step."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CheckPipelineConfig:
    team: str | None = None
    root_id: str | None = None
    full_raw: bool = False
