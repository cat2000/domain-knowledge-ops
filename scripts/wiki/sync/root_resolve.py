"""Parse Confluence URLs and resolve Space overview / ancestors."""

from __future__ import annotations

import base64
import json
import re
import urllib.error
import urllib.request
from typing import List, Optional
from urllib.parse import quote


def try_parse_page_id(url_or_id: str) -> Optional[str]:
    s = url_or_id.strip()
    if s.isdigit():
        return s
    m = re.search(r"/pages/(\d+)", s)
    if m:
        return m.group(1)
    m = re.search(r"[?&]homepageId=(\d+)", s, re.I)
    if m:
        return m.group(1)
    m = re.search(r"\b(\d{6,})\b", s)
    if m:
        return m.group(1)
    return None


def space_key_from_space_overview_url(url_or_id: str) -> Optional[str]:
    m = re.search(r"/spaces/([^/?#]+)/overview", url_or_id.strip(), re.I)
    if m:
        return m.group(1).strip()
    return None


def basic_auth_header(email: str, token: str) -> str:
    raw = f"{email}:{token}".encode()
    return "Basic " + base64.b64encode(raw).decode()


def fetch_space_homepage_page_id(
    base_wiki_url: str, auth_header: str, space_key: str
) -> str:
    api = base_wiki_url.rstrip("/")
    url = f"{api}/rest/api/space/{quote(space_key, safe='')}?expand=homepage"
    req = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "Authorization": auth_header},
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:600]
        raise RuntimeError(f"HTTP {e.code}: {body}") from e
    hp = data.get("homepage")
    if isinstance(hp, dict):
        pid = hp.get("id")
        if pid is not None and str(pid).strip().isdigit():
            return str(pid).strip()
    raw_id = data.get("homepageId")
    if raw_id is not None and str(raw_id).strip().isdigit():
        return str(raw_id).strip()
    return ""


def parse_page_id(url_or_id: str) -> str:
    r = try_parse_page_id(url_or_id)
    if r:
        return r
    raise SystemExit(
        f"Could not parse Confluence page ID from: {url_or_id!r} "
        "(expect digits, URL with /pages/<id>/, ?homepageId=<id>, or …/spaces/<KEY>/overview "
        "with ATLASSIAN_EMAIL + ATLASSIAN_API_TOKEN)."
    )


def fetch_content_json(base_wiki_url: str, auth_header: str, page_id: str) -> dict:
    api = base_wiki_url.rstrip("/")
    url = f"{api}/rest/api/content/{page_id}?expand=ancestors"
    req = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "Authorization": auth_header},
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:600]
        raise RuntimeError(f"HTTP {e.code}: {body}") from e


def fetch_space_key_for_page(base_wiki_url: str, auth_header: str, page_id: str) -> str:
    api = base_wiki_url.rstrip("/")
    url = f"{api}/rest/api/content/{page_id}?expand=space"
    req = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "Authorization": auth_header},
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:600]
        raise RuntimeError(f"HTTP {e.code}: {body}") from e
    sp = data.get("space")
    if isinstance(sp, dict) and sp.get("key"):
        return str(sp["key"]).strip()
    return ""


def fetch_ancestor_ids(base_wiki_url: str, auth_header: str, page_id: str) -> List[str]:
    data = fetch_content_json(base_wiki_url, auth_header, page_id)
    anc = data.get("ancestors") or []
    out: List[str] = []
    for item in anc:
        if isinstance(item, dict) and item.get("id"):
            out.append(str(item["id"]))
    return out
