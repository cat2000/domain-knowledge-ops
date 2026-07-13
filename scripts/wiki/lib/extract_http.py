"""Confluence page fetch HTTP helpers (no orchestration)."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional, Tuple

from wiki.lib.extract_logic import pick_body


def req_json(url: str, auth_header: str, timeout: int = 120) -> Dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "Authorization": auth_header},
    )
    with urllib.request.urlopen(request, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_page(
    base: str, auth: str, page_id: str
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    base = base.rstrip("/")
    qs = urllib.parse.urlencode(
        {
            "expand": "body.storage,body.view,space,version,history.lastUpdated",
        }
    )
    url = f"{base}/rest/api/content/{page_id}?{qs}"
    try:
        return req_json(url, auth), None
    except urllib.error.HTTPError as exc:
        err = exc.read().decode("utf-8", errors="replace")
        return None, f"HTTP {exc.code}: {err[:500]}"


def pick_page_body(data: Dict[str, Any]) -> Tuple[str, str, str]:
    return pick_body(data)
