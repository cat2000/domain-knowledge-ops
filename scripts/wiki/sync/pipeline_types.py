"""Typed plan for S1 Confluence sync (inputs, roots, artifact paths)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class SyncConfig:
    """CLI + env resolved flags (no HTTP)."""

    raw_input: str
    url_arg: Optional[str]
    skip_materialize: bool
    no_distill_handoff: bool
    fetch_attachments: bool
    attachment_pages: str
    attachment_subroot: str
    attachments_mode: Optional[str]
    allow_partial: bool
    resolve_canonical_root: bool
    no_reuse_existing_by_root: bool
    enum_mode: str
    cql: str
    enum_page_size: Optional[int]
    extract_workers: Optional[int]


@dataclass(frozen=True)
class SyncRoots:
    """Resolved page IDs and display metadata."""

    pasted_id: str
    enum_root_id: str
    storage_root_id: str
    root_label: str
    root_url: str
    used_space_overview: bool
    lifted: bool


@dataclass(frozen=True)
class SyncPaths:
    """Idempotent artifact locations under domain-knowledge (by storage root)."""

    storage_root_id: str
    extracted_base: Path
    descendants_full: Path
    subtree_enum: Path
    pages_dir: Path
    coverage_md: Path
    rules_base: Path
    extract_report: Path

    @classmethod
    def for_storage_root(cls, repo: Path, storage_root_id: str) -> SyncPaths:
        extracted_base = repo / "domain-knowledge/extracted/by-root" / storage_root_id
        return cls(
            storage_root_id=storage_root_id,
            extracted_base=extracted_base,
            descendants_full=extracted_base / "descendants-full.json",
            subtree_enum=extracted_base / "_subtree_enumeration.json",
            pages_dir=extracted_base / "pages",
            coverage_md=extracted_base / "source-coverage.md",
            rules_base=repo / "domain-knowledge/materialized/by-root" / storage_root_id,
            extract_report=extracted_base / "_last_extract_report.json",
        )

    def ensure_extracted_base(self) -> None:
        self.extracted_base.mkdir(parents=True, exist_ok=True)
