"""Pure helpers for Confluence page extract (testable without HTTP)."""

from __future__ import annotations

import math
import os
from typing import Any, Dict, Optional, Set, Tuple

from wiki.lib.confluence_plain_text import (
    html_to_readable_plain,
    storage_xml_to_readable_plain,
)


def parse_page_id_list(raw: str) -> Set[str]:
    out: Set[str] = set()
    for part in (raw or "").replace(";", ",").split(","):
        token = part.strip()
        if token.isdigit():
            out.add(token)
    return out


def auto_extract_workers(
    page_count: int,
    *,
    cpu_count: int | None = None,
    max_workers_cap: int | None = None,
) -> int:
    if page_count <= 1:
        return 1
    cpu = cpu_count if cpu_count is not None else int(os.cpu_count() or 1)
    if cpu < 1:
        cpu = 1

    hw_cap = min(16, max(2, cpu * 2))
    if max_workers_cap is not None:
        hw_cap = min(hw_cap, max(1, max_workers_cap))
    else:
        max_env = (os.environ.get("CONFLUENCE_EXTRACT_WORKERS_MAX") or "").strip()
        if max_env.isdigit():
            hw_cap = min(hw_cap, max(1, int(max_env)))

    need = max(2, math.ceil(page_count / 16))
    return max(1, min(hw_cap, need))


def choose_extract_workers(
    page_count: int,
    *,
    cli: int | None = None,
    env_workers: int | None = None,
    cpu_count: int | None = None,
    max_workers_cap: int | None = None,
) -> tuple[int, str]:
    if cli is not None:
        return max(1, int(cli)), "--workers"
    if env_workers is not None:
        return max(1, int(env_workers)), "CONFLUENCE_EXTRACT_WORKERS"
    env = (os.environ.get("CONFLUENCE_EXTRACT_WORKERS") or "").strip()
    if env.isdigit():
        return max(1, int(env)), "CONFLUENCE_EXTRACT_WORKERS"
    workers = auto_extract_workers(
        page_count, cpu_count=cpu_count, max_workers_cap=max_workers_cap
    )
    return workers, f"auto ({page_count} pages)"


def pick_body(data: Dict[str, Any]) -> Tuple[str, str, str]:
    """Returns (plain_text, source_label, note)."""
    body = data.get("body") or {}
    view = (body.get("view") or {}).get("value") or ""
    storage = (body.get("storage") or {}).get("value") or ""

    if view.strip():
        text = html_to_readable_plain(view)
        if len(text) < 40 and storage.strip():
            alt = storage_xml_to_readable_plain(storage)
            if len(alt) > len(text):
                return alt, "storage", ""
        return text, "view", ""

    if storage.strip():
        return storage_xml_to_readable_plain(storage), "storage", ""

    return (
        "",
        "empty",
        "API 未返回 body.view / body.storage 正文；可能在白板、Draw.io、附件或未展开宏中。请在 Confluence UI 核对。",
    )
