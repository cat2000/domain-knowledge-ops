"""Pure helpers for Jira fetch step (testable without HTTP)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List


def adf_to_text(node: Any) -> str:
    if node is None:
        return ""
    if isinstance(node, str):
        return node
    if isinstance(node, list):
        return "\n".join(filter(None, (adf_to_text(item) for item in node)))
    if not isinstance(node, dict):
        return ""
    node_type = node.get("type")
    if node_type == "text":
        return node.get("text") or ""
    if node_type == "hardBreak":
        return "\n"
    inner = "".join(adf_to_text(child) for child in node.get("content") or [])
    if node_type in ("paragraph", "heading", "listItem", "tableRow", "tableCell"):
        return inner + "\n"
    if node_type in ("bulletList", "orderedList"):
        return inner
    return inner


def field_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        return adf_to_text(value).strip()
    return str(value).strip()


def build_parent_index(raw_dir: Path) -> Dict[str, Any]:
    """parent_key -> {children[], summaries} from a batch of raw/*.json (no LLM)."""
    by_parent: Dict[str, Dict[str, Any]] = {}
    for path in sorted(raw_dir.glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        key = doc.get("key")
        if not key:
            continue
        parent_key = doc.get("parent_key")
        if parent_key:
            slot = by_parent.setdefault(
                parent_key,
                {"parent_key": parent_key, "children": [], "parent": doc.get("parent")},
            )
            if key not in slot["children"]:
                slot["children"].append(key)
    return {
        "by_parent": by_parent,
        "child_count": sum(len(value["children"]) for value in by_parent.values()),
    }


def parse_keys_arg(raw: str) -> List[str]:
    return [token.strip().upper() for token in re.split(r"[\s,]+", raw) if token.strip()]


def should_advance_fetch_window(
    mode: str,
    *,
    batch_count: int,
    limit: int,
    cursor: Dict[str, Any],
) -> bool:
    if mode not in ("history", "batch", "full"):
        return False
    if batch_count >= limit and cursor.get("last_key"):
        return False
    return True


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_sync_state(path: Path) -> Dict[str, Any]:
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def load_smoke_keys(smoke_keys_path: Path) -> List[str]:
    if not smoke_keys_path.is_file():
        return []
    data = json.loads(smoke_keys_path.read_text(encoding="utf-8"))
    keys = data.get("keys") or []
    return [str(key).strip().upper() for key in keys if str(key).strip()]


def advance_time_window(
    team: Dict[str, Any],
    state: Dict[str, Any],
    *,
    batch_count: int,
    limit: int,
    mode: str,
    add_months_fn,
) -> bool:
    """Advance created window when batch exhausted. Returns True if advanced."""
    if not should_advance_fetch_window(
        mode,
        batch_count=batch_count,
        limit=limit,
        cursor=state.get("cursor") or {},
    ):
        return False
    window = state.get("window") or {}
    gte, lt = window.get("created_gte"), window.get("created_lt")
    if not gte or not lt:
        return False
    months = int((team.get("jira") or {}).get("time_window_months", 3))
    state["window"] = {"created_gte": lt, "created_lt": add_months_fn(lt, months)}
    state["cursor"] = {}
    return True


def build_pipeline_handoff(
    *,
    repo_root: Path,
    jira_dir: Path,
    team_key: str,
    root_id: str,
    mode: str,
    keys: List[str],
    stage: str,
) -> Dict[str, Any]:
    checklist = jira_dir.parent / "DOMAIN_MODULE_CHECKLIST.md"
    return {
        "pipeline": "add-knowledge-from-jira",
        "version": 1,
        "stage_ingest_complete": stage in ("s1", "fetch", "ingest"),
        "stage_a_complete": stage in ("s1", "fetch", "ingest"),
        "stage_s1_complete": stage in ("s1", "fetch", "ingest"),
        "team": team_key,
        "root_id": root_id,
        "mode": mode,
        "batch_keys": keys,
        "intermediate": {
            "jira_dir": f"domain-knowledge/curated/by-root/{root_id}/jira",
            "raw_dir": f"domain-knowledge/curated/by-root/{root_id}/jira/raw",
            "materialized_dir": f"domain-knowledge/curated/by-root/{root_id}/jira/materialized",
            "attribution_dir": f"domain-knowledge/curated/by-root/{root_id}/jira/attribution",
            "checklist": str(checklist.relative_to(repo_root))
            if checklist.is_file()
            else f"domain-knowledge/curated/by-root/{root_id}/DOMAIN_MODULE_CHECKLIST.md",
        },
        "stage_b_cursor_skill": "add-knowledge-from-jira",
        "wiki_runbook": ".cursor/skills/generate-knowledge-from-wiki/RUNBOOK.md",
        "distill_quality_bar_doc": "domain-knowledge/distill-quality-bar.md",
        "attribution_model": "domain-knowledge/jira/first-principles-attribution.md",
        "chaining_contract": (
            "Classify: attribute.py + Cursor B1. "
            "Recognize + Compose: @generate-knowledge-from-wiki RUNBOOK (shared checklist). "
            "Jira business evidence enters unified Compose at S3 through S2 closure/materialized; "
            "there is no post-S6 Jira patch path."
        ),
        "parent_hierarchy": (
            "Use raw.parent_key / raw.parent / _parent_index.json (JQL parent = KEY); "
            "not only issuelinks."
        ),
        "next_steps": [
            "Classify: python3 scripts/jira/steps/attribute.py --team <team>",
            "Recognize: Cursor — DOMAIN_MODULE_CHECKLIST + closure (Wiki RUNBOOK); human 确认",
            "Compose: generate-knowledge-from-wiki RUNBOOK (S3→S6; includes Jira business evidence)",
        ],
    }
