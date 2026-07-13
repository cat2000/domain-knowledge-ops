"""Optional ancestor promotion to CONFLUENCE_CANONICAL_ROOT_IDS."""

from __future__ import annotations

import os
from typing import List, Tuple


def canonical_root_ids_from_env() -> Tuple[str, ...]:
    """Comma-separated page IDs that may be used as promotion targets; empty = no promotion."""
    raw = (os.environ.get("CONFLUENCE_CANONICAL_ROOT_IDS") or "").strip()
    if not raw or raw.lower() in ("none", "false", "0"):
        return ()
    out: List[str] = []
    for part in raw.split(","):
        x = part.strip()
        if x.isdigit():
            out.append(x)
    return tuple(dict.fromkeys(out))


def env_resolve_canonical_flag() -> bool:
    v = (os.environ.get("CONFLUENCE_RESOLVE_CANONICAL_ROOT") or "").strip().lower()
    return v in ("1", "true", "yes")


def resolve_canonical_sync_root(
    pasted_page_id: str,
    ancestor_ids: List[str],
    *,
    enabled: bool,
    canonical_root_ids: Tuple[str, ...],
) -> Tuple[str, bool]:
    if not enabled or not canonical_root_ids:
        return (pasted_page_id, False)
    if pasted_page_id in canonical_root_ids:
        return (pasted_page_id, False)
    anc = set(ancestor_ids)
    for root in canonical_root_ids:
        if root in anc:
            return (root, True)
    return (pasted_page_id, False)
