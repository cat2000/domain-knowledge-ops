"""Confluence enumeration HTTP helpers (no orchestration)."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import deque
from typing import Any, Dict, Iterator, List, Optional

from wiki.lib.enumerate_logic import compact_row, merge_enum_root_row


def req_json(url: str, auth_header: str, timeout: int = 120) -> Dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "Authorization": auth_header,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")
        print(
            "\n*** CONFLUENCE ENUMERATION FAILED (HTTP) — output JSON must not be trusted as complete ***\n",
            file=sys.stderr,
        )
        raise SystemExit(f"HTTP {exc.code} for {url}\n{err_body}") from exc
    except urllib.error.URLError as exc:
        print(
            "\n*** CONFLUENCE ENUMERATION FAILED (network / SSL / DNS) — "
            "no guarantee any --json file is complete; fix connectivity and re-run ***\n",
            file=sys.stderr,
        )
        reason = getattr(exc, "reason", exc)
        raise SystemExit(f"URLError reaching Confluence: {reason!r}\nURL: {url}") from exc
    except TimeoutError as exc:
        print(
            "\n*** CONFLUENCE ENUMERATION FAILED (timeout) — partial results invalid as full listing ***\n",
            file=sys.stderr,
        )
        raise SystemExit(f"Timeout after {timeout}s: {url}") from exc


def child_page_url(base: str, parent_id: str, limit: int, start: int) -> str:
    base = base.rstrip("/")
    path = f"{base}/rest/api/content/{parent_id}/child/page"
    qs = urllib.parse.urlencode(
        {
            "limit": str(limit),
            "start": str(start),
            "expand": "space",
        }
    )
    return f"{path}?{qs}"


def iter_child_pages(
    base: str, auth_header: str, parent_id: str, page_size: int
) -> Iterator[Dict[str, Any]]:
    start = 0
    while True:
        url = child_page_url(base, parent_id, page_size, start)
        data = req_json(url, auth_header)
        batch: List[Dict[str, Any]] = data.get("results") or []
        for item in batch:
            yield item
        if len(batch) < page_size:
            break
        start += page_size


def _resolve_search_next_url(base: str, next_link: str) -> str:
    """Turn Confluence ``_links.next`` into an absolute search URL."""
    if next_link.startswith("http://") or next_link.startswith("https://"):
        return next_link
    if next_link.startswith("/"):
        return f"{base.rstrip('/')}{next_link}"
    return f"{base.rstrip('/')}/{next_link.lstrip('/')}"


def search_pages_cql(
    base: str,
    auth_header: str,
    cql: str,
    page_size: int,
) -> List[Dict[str, Any]]:
    """Paginated CQL search via ``/rest/api/content/search``.

    Confluence Cloud ignores ``start`` for this endpoint; follow ``_links.next``
    (cursor) until exhausted. Do not stop early when ``len(batch) < limit`` — the
    first page can be short while more results remain.
    """
    base = base.rstrip("/")
    limit = max(1, min(int(page_size), 250))
    out: List[Dict[str, Any]] = []
    seen: set[str] = set()
    query = cql.strip()
    if not query:
        return out

    url: Optional[str] = (
        f"{base}/rest/api/content/search?"
        + urllib.parse.urlencode({"cql": query, "limit": str(limit), "expand": "space"})
    )

    while url:
        data = req_json(url, auth_header)
        batch: List[Dict[str, Any]] = data.get("results") or []
        if not batch:
            break

        added = 0
        for item in batch:
            page_id = str(item.get("id", "") or "")
            if page_id and page_id not in seen:
                seen.add(page_id)
                out.append(item)
                added += 1

        next_link = (data.get("_links") or {}).get("next")
        if not next_link or added == 0:
            break
        url = _resolve_search_next_url(base, str(next_link))

    return out


def enumerate_descendants(
    base: str,
    auth_header: str,
    root_id: str,
    page_size: int,
) -> List[Dict[str, Any]]:
    """BFS from root; returns child pages only (root merged later)."""
    out: List[Dict[str, Any]] = []
    seen: set[str] = {str(root_id)}
    queue: deque[str] = deque([str(root_id)])

    while queue:
        parent_id = queue.popleft()
        for child in iter_child_pages(base, auth_header, parent_id, page_size):
            page_id = str(child.get("id", ""))
            if not page_id or page_id in seen:
                continue
            seen.add(page_id)
            if page_id == str(root_id):
                continue
            out.append(child)
            queue.append(page_id)

    return out


def fetch_one_page_compact(
    base: str, auth_header: str, page_id: str, wiki_base: str
) -> Dict[str, Any]:
    base = base.rstrip("/")
    url = f"{base}/rest/api/content/{page_id.strip()}?expand=space"
    data = req_json(url, auth_header)
    return compact_row(data, wiki_base)


def ensure_enum_root_included(
    compact: List[Dict[str, Any]],
    base: str,
    auth_header: str,
    wiki_base: str,
    root_id: str,
) -> List[Dict[str, Any]]:
    rid = str(root_id).strip()
    if not rid:
        return compact
    have = {str(row.get("id", "")) for row in compact}
    if rid in have:
        return compact
    try:
        root_row = fetch_one_page_compact(base, auth_header, rid, wiki_base)
    except SystemExit as exc:
        print(
            f"enumerate: failed to fetch root page {rid} for merge: {exc}",
            file=sys.stderr,
        )
        return compact
    return merge_enum_root_row(compact, rid, root_row)
