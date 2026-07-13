"""HTTP client for Jira REST (no orchestration)."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from jira.lib.jira_fetch_logic import field_text

SEARCH_FIELDS = [
    "summary",
    "description",
    "created",
    "updated",
    "issuetype",
    "parent",
    "status",
    "labels",
    "components",
    "issuelinks",
    "comment",
]

PARENT_META_FIELDS = "summary,issuetype,parent,status"


def http_json(
    method: str,
    url: str,
    auth: str,
    body: Optional[Dict[str, Any]] = None,
) -> Any:
    data = None
    headers = {
        "Accept": "application/json",
        "Authorization": auth,
        "Content-Type": "application/json",
    }
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Jira HTTP {exc.code} for {url}:\n{err_body[:2000]}") from exc


def search_issues(
    jql: str,
    auth: str,
    api_base: str,
    max_results: int,
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    next_token: Optional[str] = None
    fields_csv = ",".join(SEARCH_FIELDS)
    while len(out) < max_results:
        take = min(100, max_results - len(out))
        url = (
            f"{api_base}/search/jql?jql={quote(jql)}"
            f"&maxResults={take}&fields={quote(fields_csv)}"
        )
        if next_token:
            url += f"&nextPageToken={quote(next_token)}"
        data = http_json("GET", url, auth)
        issues = data.get("issues") or []
        if not issues:
            break
        out.extend(issues)
        next_token = data.get("nextPageToken")
        if not next_token:
            break
    return out


def fetch_all_comments(issue_key: str, auth: str, api_base: str) -> List[Dict[str, Any]]:
    comments: List[Dict[str, Any]] = []
    start_at = 0
    while True:
        url = (
            f"{api_base}/issue/{issue_key}/comment"
            f"?startAt={start_at}&maxResults=100&orderBy=created"
        )
        data = http_json("GET", url, auth)
        batch = data.get("comments") or []
        for comment in batch:
            comments.append(
                {
                    "id": comment.get("id"),
                    "author": (comment.get("author") or {}).get("displayName"),
                    "created": comment.get("created"),
                    "updated": comment.get("updated"),
                    "body": comment.get("body"),
                    "body_text": field_text(comment.get("body")),
                }
            )
        total = int(data.get("total") or 0)
        start_at += len(batch)
        if start_at >= total or not batch:
            break
    return comments


def fetch_issue_meta(key: str, auth: str, api_base: str, fields: str) -> Dict[str, Any]:
    url = f"{api_base}/issue/{key}?fields={fields}"
    data = http_json("GET", url, auth)
    return data.get("fields") or {}


def fetch_issue_by_key(key: str, auth: str, api_base: str) -> Dict[str, Any]:
    url = f"{api_base}/issue/{key}?fields={','.join(SEARCH_FIELDS)}"
    return http_json("GET", url, auth)


def resolve_parent_record(
    parent: Dict[str, Any],
    auth: str,
    api_base: str,
    *,
    resolve_chain: bool = False,
    max_depth: int = 8,
) -> tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
    key = (parent or {}).get("key")
    if not key:
        return None, []

    def _one(issue_key: str, embedded: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        fields = (embedded or {}).get("fields") if embedded else None
        if not fields or not fields.get("summary"):
            fields = fetch_issue_meta(issue_key, auth, api_base, PARENT_META_FIELDS)
        grand = fields.get("parent") or {}
        return {
            "key": issue_key,
            "summary": fields.get("summary"),
            "issuetype": (fields.get("issuetype") or {}).get("name"),
            "status": (fields.get("status") or {}).get("name"),
            "parent_key": grand.get("key"),
        }

    immediate = _one(key, parent if parent.get("fields") else None)
    chain: List[Dict[str, Any]] = [immediate]
    if not resolve_chain:
        return immediate, chain

    seen = {key}
    cursor_key = immediate.get("parent_key")
    while cursor_key and len(chain) < max_depth:
        if cursor_key in seen:
            break
        seen.add(cursor_key)
        record = _one(cursor_key)
        chain.append(record)
        cursor_key = record.get("parent_key")
    chain.reverse()
    return immediate, chain


def normalize_issue(
    issue: Dict[str, Any],
    auth: str,
    api_base: str,
    *,
    refetch_comments: bool = True,
    resolve_parent_chain: bool = False,
) -> Dict[str, Any]:
    from datetime import datetime, timezone

    key = issue.get("key") or ""
    fields = issue.get("fields") or {}
    if refetch_comments:
        comments = fetch_all_comments(key, auth, api_base)
    else:
        comments = []
        for comment in (fields.get("comment") or {}).get("comments") or []:
            comments.append(
                {
                    "id": comment.get("id"),
                    "author": (comment.get("author") or {}).get("displayName"),
                    "created": comment.get("created"),
                    "updated": comment.get("updated"),
                    "body": comment.get("body"),
                    "body_text": field_text(comment.get("body")),
                }
            )

    parent_field = fields.get("parent") or {}
    parent_rec, parent_chain = resolve_parent_record(
        parent_field,
        auth,
        api_base,
        resolve_chain=resolve_parent_chain,
    )
    issuetype = fields.get("issuetype") or {}
    hierarchy_root = (
        parent_chain[0]["key"] if resolve_parent_chain and parent_chain else None
    )
    return {
        "key": key,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "summary": fields.get("summary"),
        "status": (fields.get("status") or {}).get("name"),
        "issuetype": issuetype.get("name"),
        "created": fields.get("created"),
        "updated": fields.get("updated"),
        "labels": fields.get("labels") or [],
        "components": [
            (component.get("name") if isinstance(component, dict) else component)
            for component in (fields.get("components") or [])
        ],
        "parent_key": parent_rec.get("key") if parent_rec else None,
        "parent": parent_rec,
        "parent_chain": parent_chain,
        "hierarchy_root_key": hierarchy_root,
        "description": fields.get("description"),
        "description_text": field_text(fields.get("description")),
        "comments": comments,
        "issuelinks": fields.get("issuelinks"),
    }


def http_bytes(url: str, auth: str, timeout: int = 120) -> bytes:
    req = urllib.request.Request(url, headers={"Authorization": auth})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Jira HTTP {exc.code} for {url}:\n{err_body[:2000]}") from exc


def fetch_issue_comments(
    api_base: str,
    issue_key: str,
    auth: str,
    *,
    max_results: int = 100,
) -> dict:
    """Paginate GET /rest/api/3/issue/{key}/comment."""
    all_items: list[dict] = []
    start_at = 0
    total: int | None = None
    while True:
        query = urllib.parse.urlencode(
            {
                "startAt": str(start_at),
                "maxResults": str(max_results),
                "expand": "renderedBody",
            }
        )
        url = f"{api_base.rstrip('/')}/issue/{quote(issue_key)}/comment?{query}"
        page = http_json("GET", url, auth)
        batch = page.get("comments") or []
        if total is None:
            total = int(page.get("total", len(batch)))
        all_items.extend(batch)
        if not batch or start_at + len(batch) >= (total or 0):
            break
        start_at += len(batch)
    return {
        "issueKey": issue_key,
        "total": len(all_items),
        "comments": all_items,
    }
