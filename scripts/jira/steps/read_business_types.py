"""Types for read_business step."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReadBusinessConfig:
    team: str = ""
    theme: str | None = None
    confirmed_only: bool = False
