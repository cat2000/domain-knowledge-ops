"""Pure helpers for materialized/*.md generation from extracted pages."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

from wiki.lib.confluence_plain_text import clean_leaked_markup_tokens, normalize_document


def parse_frontmatter(raw: str) -> Tuple[Dict[str, str], str]:
    if not raw.startswith("---\n"):
        return {}, raw
    end = raw.find("\n---\n", 4)
    if end == -1:
        return {}, raw
    front_matter_raw = raw[4:end]
    body = raw[end + 5 :]
    out: Dict[str, str] = {}
    for line in front_matter_raw.splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                value = value.strip("\"'")
        out[key] = value
    return out, body


def is_skip_outline(value: str) -> bool:
    normalized = value.strip()
    return normalized in ("", "—", '"—"', "'—'", "-")


def safe_rules_path(rules_base: Path, relative: str) -> Path:
    rel = relative.replace("\\", "/").lstrip("/")
    if not rel.endswith(".md"):
        raise ValueError(f"Not a .md path: {relative}")
    if ".." in rel.split("/") or rel.startswith("/"):
        raise ValueError(f"Unsafe path: {relative}")
    if rel.upper().endswith("README.MD"):
        raise ValueError(f"Refusing to write README: {relative}")
    out = (rules_base / rel).resolve()
    base_resolved = rules_base.resolve()
    if not str(out).startswith(str(base_resolved)):
        raise ValueError(f"Path escapes rules base: {relative}")
    return out


def polish_rule_body(text: str) -> str:
    return normalize_document(clean_leaked_markup_tokens(text))


def strip_extract_heading(body: str) -> str:
    body = body.strip()
    match = re.match(
        r"^##\s+正文（Confluence REST 提取）\s*\n+", body, re.MULTILINE
    )
    if match:
        body = body[match.end() :]
    body = re.sub(r"^<!--.*?-->\s*", "", body.strip(), count=1, flags=re.DOTALL)
    return body.strip()


def render_materialized_markdown(stem_title: str, pages: List[Dict[str, Any]]) -> str:
    lines: List[str] = [
        f"# {stem_title}",
        "",
    ]
    for index, page in enumerate(pages):
        title = str(page["title"])
        web_ui = str(page.get("web_ui") or "").strip()
        if web_ui:
            lines.append(f"### [{title}]({web_ui})")
        else:
            lines.append(f"### {title}")
        lines.append("")
        lines.append(
            page.get("body") or "_（此页无可用正文；请在 Confluence 查看原页。）_"
        )
        lines.append("")
        if index < len(pages) - 1:
            lines.append("---")
            lines.append("")
    return "\n".join(lines) + "\n"
