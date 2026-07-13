"""Pure helpers for Confluence page enumeration (no HTTP)."""

from __future__ import annotations

from typing import Any, Dict, List


def compact_row(page: Dict[str, Any], wiki_base: str) -> Dict[str, Any]:
    space_key = ""
    try:
        space_key = (page.get("space") or {}).get("key") or ""
    except Exception:
        pass
    title = page.get("title") or ""
    page_id = str(page.get("id", ""))
    webui_path = ""
    try:
        webui_path = (page.get("_links") or {}).get("webui") or ""
    except Exception:
        pass
    if webui_path.startswith("/"):
        web_ui = wiki_base.rstrip("/") + webui_path
    elif space_key:
        web_ui = f"{wiki_base.rstrip('/')}/spaces/{space_key}/pages/{page_id}/"
    else:
        web_ui = ""
    return {
        "id": page_id,
        "title": title,
        "spaceKey": space_key,
        "webUi": web_ui,
    }


def merge_enum_root_row(
    compact: List[Dict[str, Any]],
    root_id: str,
    root_row: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Prepend enumeration root when ``root_id`` is absent from ``compact``."""
    rid = str(root_id).strip()
    if not rid:
        return compact
    have = {str(row.get("id", "")) for row in compact}
    if rid in have:
        return compact
    return [root_row] + compact
