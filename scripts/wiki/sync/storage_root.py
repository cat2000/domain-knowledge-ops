"""Reuse existing by-root/ storage when syncing a subtree."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

from wiki.sync.canonical import canonical_root_ids_from_env
from runtime.paths import REPO_ROOT
from wiki.sync.root_resolve import basic_auth_header, fetch_ancestor_ids


def extracted_by_root_base() -> Path:
    return REPO_ROOT / "domain-knowledge" / "extracted" / "by-root"


def roots_containing_page(page_id: str) -> List[str]:
    out: List[str] = []
    roots_base = extracted_by_root_base()
    if not roots_base.is_dir():
        return out
    target = f"{page_id}.md"
    for child in sorted(roots_base.iterdir()):
        if not child.is_dir():
            continue
        if (child / "pages" / target).is_file():
            out.append(child.name)
    return out


def choose_storage_root(candidates: List[str]) -> str:
    if len(candidates) == 1:
        return candidates[0]
    canonical = canonical_root_ids_from_env()
    for c in canonical:
        if c in candidates:
            return c
    best = candidates[0]
    best_n = -1
    for rid in candidates:
        pdir = extracted_by_root_base() / rid / "pages"
        n = len(list(pdir.glob("*.md"))) if pdir.is_dir() else 0
        if n > best_n:
            best_n = n
            best = rid
    return best


def resolve_storage_root_for_subtree(
    enum_root_id: str,
    wiki_base: str,
    reuse_enabled: bool,
) -> Tuple[str, bool]:
    if not reuse_enabled:
        return enum_root_id, False

    email = os.environ.get("ATLASSIAN_EMAIL", "").strip()
    token = os.environ.get("ATLASSIAN_API_TOKEN", "").strip()
    auth = basic_auth_header(email, token) if email and token else ""

    ids_to_try: List[str] = [enum_root_id]
    if auth:
        try:
            ids_to_try.extend(fetch_ancestor_ids(wiki_base, auth, enum_root_id))
        except Exception as exc:
            print(
                f"sync_domain_knowledge_from_confluence: reuse lookup could not fetch ancestors ({exc})",
                file=sys.stderr,
            )

    for pid in ids_to_try:
        roots = roots_containing_page(pid)
        if not roots:
            continue
        chosen = choose_storage_root(roots)
        print(
            f"sync_domain_knowledge_from_confluence: reuse storage root {chosen} "
            f"(matched pages/{pid}.md; enumeration root {enum_root_id})",
            file=sys.stderr,
        )
        return chosen, True

    return enum_root_id, False


def merge_descendants_rows(
    existing: List[Dict[str, Any]], incoming: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    by_id: Dict[str, Dict[str, Any]] = {}
    for row in existing:
        if isinstance(row, dict) and row.get("id") is not None:
            by_id[str(row["id"])] = row
    for row in incoming:
        if isinstance(row, dict) and row.get("id") is not None:
            by_id[str(row["id"])] = row
    return sorted(by_id.values(), key=lambda x: int(str(x["id"])))
