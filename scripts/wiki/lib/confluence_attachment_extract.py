#!/usr/bin/env python3
"""
Confluence page attachments: list, download, extract text by file type.

Also scans **body.view** / **body.storage** for `ri:filename="…"` and
`/download/attachments/<pageId>/…` references. When **child/attachment** REST
returns nothing (or misses an embedded image), these filenames are still
downloaded from the same page — fixes “页面里看得到 PNG、附件列表却为空”类页面。

Design goals:
- **Pluggable handlers** keyed by extension (and optional user override map).
- **Inventory file** updated each run with seen extensions / MIME / handled vs skipped,
  so new attachment types surface automatically for humans to add handlers or overrides.

Optional deps (install for broader support; see scripts/requirements-kb-attachments.txt):
- openpyxl → .xlsx
- pypdf → .pdf
- pillow + pytesseract + **系统已安装 Tesseract**（含中文包）→ `.png` / `.jpg` / … 本地 OCR，无 API 费用

环境变量：`CONFLUENCE_IMAGE_OCR=0` 关闭 OCR；`CONFLUENCE_OCR_LANG` 默认 `chi_sim+eng`；
`CONFLUENCE_OCR_MAX_PIXELS` 缩小超大图以防内存峰值。
"""

from __future__ import annotations

import csv
import io
import json
import os
import re
import threading
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

# Read-modify-write on shared inventory JSON (parallel extract workers).
_inventory_merge_lock = threading.Lock()

from wiki.lib.attachment_logic import (
    DEFAULT_EXTENSION_TO_HANDLER,
    HANDLER_MAP_FILENAME,
    INVENTORY_DEFAULT_NAME,
    attachment_download_url,
    discover_filenames_from_body_markup,
    extract_bytes,
    load_user_handler_map,
    merge_synthetic_attachments,
    resolve_handler_id,
    safe_ext,
)

_load_user_handler_map = load_user_handler_map
_merge_synthetic_attachments = merge_synthetic_attachments
_safe_ext = safe_ext

def merge_inventory(
    path: Path,
    page_id: str,
    filename: str,
    ext: str,
    media_type: str,
    handler_id: str,
    status: str,
    detail: str,
) -> None:
    with _inventory_merge_lock:
        _merge_inventory_unlocked(
            path,
            page_id,
            filename,
            ext,
            media_type,
            handler_id,
            status,
            detail,
        )


def _merge_inventory_unlocked(
    path: Path,
    page_id: str,
    filename: str,
    ext: str,
    media_type: str,
    handler_id: str,
    status: str,
    detail: str,
) -> None:
    payload: Dict[str, Any]
    if path.is_file():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            payload = {}
    else:
        payload = {}
    payload.setdefault("version", 1)
    payload.setdefault("seen_extensions", {})
    se = payload["seen_extensions"]
    if not isinstance(se, dict):
        se = {}
        payload["seen_extensions"] = se

    key = ext.lower() if ext else "(no_ext)"
    bucket = se.setdefault(
        key,
        {
            "count": 0,
            "handled_ok": 0,
            "handled_partial": 0,
            "skipped": 0,
            "unsupported": 0,
            "errors": 0,
            "media_types": {},
            "sample_files": [],
            "last_pages": [],
        },
    )
    bucket["count"] = int(bucket.get("count", 0)) + 1
    mt = media_type or ""
    if mt:
        bucket.setdefault("media_types", {})
        bucket["media_types"][mt] = int(bucket["media_types"].get(mt, 0)) + 1

    st = status.lower()
    if st == "ok":
        bucket["handled_ok"] = int(bucket.get("handled_ok", 0)) + 1
    elif st in ("skipped",):
        bucket["skipped"] = int(bucket.get("skipped", 0)) + 1
    elif st in ("unsupported",):
        bucket["unsupported"] = int(bucket.get("unsupported", 0)) + 1
    else:
        bucket["errors"] = int(bucket.get("errors", 0)) + 1

    sf = bucket.setdefault("sample_files", [])
    sample = f"{filename}"
    if isinstance(sf, list) and sample not in sf[:50]:
        sf.insert(0, sample)
        bucket["sample_files"] = sf[:30]

    lp = bucket.setdefault("last_pages", [])
    if isinstance(lp, list) and page_id not in lp[:50]:
        lp.insert(0, page_id)
        bucket["last_pages"] = lp[:25]

    bucket["last_handler_try"] = handler_id or ""
    bucket["last_status"] = status
    bucket["last_detail"] = detail[:300]

    from datetime import datetime, timezone

    payload["last_updated_utc"] = datetime.now(timezone.utc).strftime(
        "%Y-%m-%dT%H:%MZ"
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def req_binary(url: str, auth_header: str, timeout: int = 120) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"Authorization": auth_header},
    )
    with urllib.request.urlopen(request, timeout=timeout) as resp:
        return resp.read()


def iter_attachment_meta(
    wiki_base: str, auth_header: str, page_id: str, sleep_s: float
) -> List[Dict[str, Any]]:
    """Return attachment objects from Confluence REST (paginated)."""
    import time

    wiki_base = wiki_base.rstrip("/")
    out: List[Dict[str, Any]] = []
    start = 0
    limit = 50
    while True:
        qs = urllib.parse.urlencode({"limit": limit, "start": start})
        url = f"{wiki_base}/rest/api/content/{page_id}/child/attachment?{qs}"
        req = urllib.request.Request(
            url,
            headers={"Accept": "application/json", "Authorization": auth_header},
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError:
            break
        results = data.get("results") or []
        out.extend(results)
        if len(results) < limit:
            break
        start += limit
        if sleep_s > 0:
            time.sleep(sleep_s)
    return out


def extract_page_attachments(
    *,
    wiki_base: str,
    auth_header: str,
    page_id: str,
    sleep_s: float,
    max_bytes: int,
    inventory_path: Path,
    repo_root: Path,
    body_view: str = "",
    body_storage: str = "",
) -> Tuple[str, List[str]]:
    """
    Returns (markdown_append, stderr_lines).
    """
    user_map = _load_user_handler_map(repo_root)
    meta_list = iter_attachment_meta(wiki_base, auth_header, page_id, sleep_s)
    meta_list = _merge_synthetic_attachments(meta_list, page_id, body_view, body_storage)
    if not meta_list:
        return "", []

    lines: List[str] = [
        "",
        "---",
        "",
        "## 附件抽取（自动）",
        "",
        "以下为 Confluence **页面附件**及 **正文/storage 中引用的同页附件链接**（`ri:filename` / `/download/attachments/<本页ID>/…`）经脚本解析后的文本（**图片**走本地 Tesseract OCR）。REST **child/attachment** 若为空仍会尝试正文引用。详见 `attachment-type-inventory.json`。",
        "",
    ]
    err_lines: List[str] = []

    for att in meta_list:
        fname = att.get("title") or "attachment"
        ext = _safe_ext(fname)
        media_type = ""
        try:
            media_type = (att.get("metadata") or {}).get("mediaType") or ""
        except Exception:
            pass

        sz = int((att.get("extensions") or {}).get("fileSize") or 0)
        if sz and sz > max_bytes:
            merge_inventory(
                inventory_path,
                page_id,
                fname,
                ext,
                media_type,
                "",
                "skipped",
                f"too_large>{max_bytes}",
            )
            lines.append(f"### `{fname}`")
            lines.append(f"_跳过（>{max_bytes} bytes）。_")
            lines.append("")
            continue

        url = attachment_download_url(wiki_base, page_id, att)
        try:
            blob = req_binary(url, auth_header)
        except Exception as e:
            merge_inventory(
                inventory_path,
                page_id,
                fname,
                ext,
                media_type,
                "",
                "error",
                str(e),
            )
            lines.append(f"### `{fname}`")
            lines.append(f"_下载失败：{e}_")
            lines.append("")
            err_lines.append(f"{page_id} {fname}: download {e}")
            continue

        if len(blob) > max_bytes:
            merge_inventory(
                inventory_path,
                page_id,
                fname,
                ext,
                media_type,
                "",
                "skipped",
                f"too_large>{max_bytes}",
            )
            lines.append(f"### `{fname}`")
            lines.append(f"_跳过（>{max_bytes} bytes）。_")
            lines.append("")
            continue

        hid = resolve_handler_id(ext, user_map)
        if not hid:
            merge_inventory(
                inventory_path,
                page_id,
                fname,
                ext,
                media_type,
                "",
                "unsupported",
                "no_handler_for_extension",
            )
            lines.append(f"### `{fname}`")
            lines.append(
                f"_未注册处理器（扩展名 `{ext or '无'}`）。可将该类型加入 `scripts/wiki/confluence_attachment_handler_map.json`"
                f"（可复制 `scripts/wiki/confluence_attachment_handler_map.example.json`）"
                f"或扩展 `wiki/lib/attachment_logic.py` 中的 `DEFAULT_EXTENSION_TO_HANDLER`。_"
            )
            lines.append("")
            continue

        text, status, detail = extract_bytes(hid, blob)
        merge_inventory(
            inventory_path,
            page_id,
            fname,
            ext,
            media_type,
            hid,
            status,
            detail,
        )

        lines.append(f"### `{fname}`")
        lines.append(f"_处理器：`{hid}` · 状态：`{status}` · {detail}_")
        lines.append("")
        if status == "ok" and text.strip():
            lines.append(text.strip())
        elif status == "unsupported":
            lines.append(
                f"_未能提取（{detail}）。安装可选依赖见 `scripts/requirements-kb-attachments.txt` 或在 handler map 中改为 `skip`。 _"
            )
        elif status == "skipped":
            lines.append("_跳过。_")
        else:
            lines.append(f"_无正文或失败：{detail}_")
        lines.append("")

    return "\n".join(lines), err_lines
