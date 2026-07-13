#!/usr/bin/env python3
"""PIPELINE_HANDOFF.json for Cursor S1-S7 pipeline."""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = next(p for p in Path(__file__).resolve().parents if (p / "_install.py").is_file())
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
import _install

_install.bootstrap(__file__)

import json
from typing import Optional

from runtime.domain_knowledge_paths import (
    CURATED_BY_ROOT,
    DOMAIN_MODULE_CHECKLIST_FILE,
    MATERIALIZATION_CLOSURE_FILE,
    NON_BUSINESS_HEADING,
    S2_LABEL,
)
from runtime.skill_names import WIKI_SKILL  # noqa: E402
from runtime.paths import REPO_ROOT


def repo_rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path)


def write_pipeline_handoff(
    page_id: str,
    extracted_base: Path,
    materialized_base: Path,
    *,
    enumeration_root_page_id: Optional[str] = None,
    rules_base: Path | None = None,
    s1_status: str = "complete",
    extract_error_count: int = 0,
) -> Path:
    """Write handoff after S1. ``materialized_base`` is ``domain-knowledge/materialized/by-root/<id>/``."""
    if rules_base is not None and materialized_base != rules_base:
        materialized_base = rules_base
    curated = CURATED_BY_ROOT / page_id
    quality_bar = REPO_ROOT / "domain-knowledge/distill-quality-bar.md"
    distill_quality_doc = (
        repo_rel(quality_bar) if quality_bar.is_file() else "domain-knowledge/distill-quality-bar.md"
    )
    skeleton = REPO_ROOT / "domain-knowledge/distill-document-skeleton.md"
    distill_skeleton_doc = (
        repo_rel(skeleton) if skeleton.is_file() else "domain-knowledge/distill-document-skeleton.md"
    )
    payload = {
        "pipeline": WIKI_SKILL,
        "version": 5,
        "s1_status": s1_status,
        "s1_complete": s1_status == "complete",
        "extract_error_count": extract_error_count,
        "root_page_id": page_id,
        "intermediate": {
            "extracted_dir": repo_rel(extracted_base),
            "materialized_dir": repo_rel(materialized_base),
        },
        "cursor_skill": f"{WIKI_SKILL}/RUNBOOK.md (S1-S7)",
        "cursor_reads_from": f"domain-knowledge/materialized/by-root/{page_id}/",
        "cursor_writes_to": repo_rel(curated),
        "distill_phases": (
            f"S1 sync materialized/; S2 {S2_LABEL}+checklist; gate 确认; "
            "S3 _aggregate/ (确认 only); S4 domain model; S5 work draft; "
            "S6 source-language brief; S7 locale brief (deliverable_locale)"
        ),
        "distill_quality_bar_doc": distill_quality_doc,
        "distill_document_skeleton_doc": distill_skeleton_doc,
        "distill_quality_contract": (
            f"Follow {WIKI_SKILL}/RUNBOOK.md: S1 sync; S2 tag+checklist (no translation); "
            "recommended script: python3 scripts/distill/s2_recognize.py --root-id <R>; "
            f"human 确认 on {DOMAIN_MODULE_CHECKLIST_FILE}; S3 _aggregate/ for 确认 slugs only; "
            "S4/S5 _deliver work draft (readable, complete, no translation); "
            "S6 source-language brief (*-source-brief.md); "
            "S7 locale brief (*-领域知识定稿.md / *-domain-brief.md) only. "
            "distill-quality-bar.md + strategy.md; "
            f"{MATERIALIZATION_CLOSURE_FILE} required; non-business stub with {NON_BUSINESS_HEADING}. "
            "S2 must produce S2_DECISION_LEDGER.json + S2_REVIEW_DECISIONS.json. "
            "Compose gate: if checklist has 待确认, proposition_extract blocks by default. "
            "domain_check: coverage after S2; full distill after S7."
        ),
        "curated_not_from_s1": (
            "S1 orchestrator never writes curated/. Cursor writes _aggregate/ and _deliver/ per RUNBOOK."
        ),
        "chaining_contract": (
            f"After complete S1 script, same chat runs RUNBOOK S2 ({S2_LABEL}) then pauses for human 确认; "
            "partial S1 handoff blocks S2 unless the operator explicitly accepts missing source pages; "
            "继续 runs S3→S4→S5→S6→S7 for 确认 slugs only (Cursor, no HTTP LLM script)."
        ),
    }
    if enumeration_root_page_id and str(enumeration_root_page_id) != str(page_id):
        payload["enumeration_root_page_id"] = str(enumeration_root_page_id)
    path = extracted_base / "PIPELINE_HANDOFF.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
