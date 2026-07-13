"""Pure helpers: Jira raw JSON → faithful materialized markdown (no LLM)."""

from __future__ import annotations

from typing import Any


def comment_heading(comment: dict[str, Any]) -> str:
    author = comment.get("author") or "unknown"
    created = comment.get("created") or ""
    return f"{author} · {created}".strip(" ·")


def raw_ticket_to_markdown(doc: dict[str, Any]) -> str:
    key = doc.get("key") or "UNKNOWN"
    summary = (doc.get("summary") or "").strip()
    lines = [
        "---",
        f"key: {key}",
        f"summary: {summary!r}",
        f"status: {doc.get('status') or ''}",
        f"issuetype: {doc.get('issuetype') or ''}",
        f"parent_key: {doc.get('parent_key') or ''}",
        f"created: {doc.get('created') or ''}",
        f"updated: {doc.get('updated') or ''}",
        "---",
        "",
        f"# {key} · {summary}",
        "",
    ]
    parent = doc.get("parent") or {}
    if parent.get("key"):
        parent_summary = (parent.get("summary") or "")[:120]
        lines.extend([f"> Parent: `{parent['key']}` — {parent_summary}", ""])

    lines.append("## Description")
    lines.append("")
    description = (doc.get("description_text") or "").strip()
    lines.append(description if description else "_（无描述）_")
    lines.append("")

    comments = doc.get("comments") or []
    lines.append(f"## Comments ({len(comments)})")
    lines.append("")
    if not comments:
        lines.append("_（无评论）_")
        lines.append("")
    else:
        for index, comment in enumerate(comments, start=1):
            lines.append(f"### {index}. {comment_heading(comment)}")
            lines.append("")
            body = (comment.get("body_text") or "").strip()
            lines.append(body if body else "_（空）_")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"
