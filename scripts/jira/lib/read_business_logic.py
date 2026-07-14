"""Pure helpers for read_business omission scan (no I/O)."""

from __future__ import annotations

import re
from collections import defaultdict

from runtime.atlassian_env import jira_browse_base


def themes_from_attribution(
    tickets: dict[str, dict],
    allowed: frozenset[str],
) -> list[str]:
    """Theme slugs present in attribution index (Classify prep; not checklist 确认)."""
    seen: set[str] = set()
    for record in tickets.values():
        primary = record.get("primary")
        if isinstance(primary, str) and primary.strip():
            slug = primary.strip()
            if slug in allowed:
                seen.add(slug)
        for theme in record.get("themes") or []:
            if isinstance(theme, str) and theme.strip() and theme.strip() in allowed:
                seen.add(theme.strip())
    return sorted(seen)


THEME_PATTERNS: dict[str, list[tuple[str, str]]] = {}
# Pack ships no tenant omission clusters. Optional patterns belong in teams/<team>.json.

def full_text(raw: dict) -> str:
    parts = [raw.get("summary") or "", raw.get("description_text") or ""]
    for comment in raw.get("comments") or []:
        parts.append(comment.get("body_text") or "")
    return "\n".join(parts)


def text_length(raw: dict) -> int:
    return len((raw.get("description_text") or "").strip()) + sum(
        len((comment.get("body_text") or "").strip()) for comment in raw.get("comments") or []
    )


def scan_theme(
    theme: str,
    keys: list[str],
    raw_by_key: dict[str, dict],
    parent_idx: dict,
    idx: dict,
    *,
    locale: str = "en",
) -> str:
    patterns = THEME_PATTERNS.get(theme, [])
    cluster_keys: dict[str, list[str]] = {name: [] for name, _ in patterns}
    cluster_keys["_other"] = []
    substance: list[tuple[str, int, str]] = []

    for key in keys:
        raw = raw_by_key.get(key, {})
        blob = full_text(raw)
        text_len = text_length(raw)
        if text_len > 80:
            substance.append((key, text_len, (raw.get("summary") or "")[:70]))

        matched = False
        for name, pattern in patterns:
            if re.search(pattern, blob, re.I):
                cluster_keys[name].append(key)
                matched = True
                break
        if not matched:
            cluster_keys["_other"].append(key)

    browse = jira_browse_base()
    substance.sort(key=lambda item: -item[1])
    by_parent: dict[str, list[str]] = defaultdict(list)
    for key in keys:
        parent = idx[key].get("parent") or "_orphan"
        by_parent[parent].append(key)
    top_parents = sorted(by_parent.items(), key=lambda item: -len(item[1]))[:10]

    if locale == "zh-CN":
        return _render_scan_theme_zh(
            theme, keys, raw_by_key, parent_idx, patterns, cluster_keys, substance, browse, top_parents
        )
    return _render_scan_theme_en(
        theme, keys, raw_by_key, parent_idx, patterns, cluster_keys, substance, browse, top_parents
    )


def _render_scan_theme_en(
    theme: str,
    keys: list[str],
    raw_by_key: dict[str, dict],
    parent_idx: dict,
    patterns: list[tuple[str, str]],
    cluster_keys: dict[str, list[str]],
    substance: list[tuple[str, int, str]],
    browse: str,
    top_parents: list[tuple[str, list[str]]],
) -> str:
    lines = [
        f"# {theme} · gap scan (read {len(keys)} business_extract tickets)\n\n",
        "> Script `jira_read_business_tickets.py` **reads every ticket's** `raw/<KEY>.json` "
        "`summary` + `description_text` + **all** `comments[].body_text`.\n\n",
    ]

    lines.append("## Cluster coverage (ticket count)\n\n")
    for name, _ in patterns:
        cluster = cluster_keys[name]
        lines.append(f"- **{name}**: {len(cluster)}\n")
    lines.append(f"- **Unmatched by clusters above**: {len(cluster_keys['_other'])}\n\n")

    lines.append("## Substantive tickets (description+comments >80 chars · prioritize manual review)\n\n")
    for key, char_count, summary in substance[:40]:
        lines.append(
            f"- [{key}]({browse}/browse/{key}) ({char_count} chars) {summary}\n"
        )
    if len(substance) > 40:
        lines.append(f"- … and {len(substance) - 40} more\n")

    lines.append("\n## Clustered by parent Epic (top 10)\n\n")
    for parent, parent_keys in top_parents:
        if parent == "_orphan":
            label = "_orphan"
        elif parent in parent_idx:
            label = f"{parent} — {(parent_idx[parent].get('parent') or {}).get('summary', '')[:60]}"
        else:
            label = parent
        lines.append(f"### {label} ({len(parent_keys)})\n\n")
        for ticket_key in sorted(parent_keys)[:15]:
            raw = raw_by_key.get(ticket_key, {})
            lines.append(f"- `{ticket_key}` · {raw.get('summary', '')[:72]}\n")
        if len(parent_keys) > 15:
            lines.append(f"- … +{len(parent_keys) - 15}\n")
        lines.append("\n")

    return "".join(lines)


def _render_scan_theme_zh(
    theme: str,
    keys: list[str],
    raw_by_key: dict[str, dict],
    parent_idx: dict,
    patterns: list[tuple[str, str]],
    cluster_keys: dict[str, list[str]],
    substance: list[tuple[str, int, str]],
    browse: str,
    top_parents: list[tuple[str, list[str]]],
) -> str:
    lines = [
        f"# {theme} · 遗漏扫描（通读 {len(keys)} 张 business_extract）\n\n",
        "> 脚本 `jira_read_business_tickets.py` **逐张读取** `raw/<KEY>.json` 的 "
        "`summary` + `description_text` + **全部** `comments[].body_text`。\n\n",
    ]

    lines.append("## 主题簇覆盖（张数）\n\n")
    for name, _ in patterns:
        cluster = cluster_keys[name]
        lines.append(f"- **{name}**：{len(cluster)} 张\n")
    lines.append(f"- **未命中上述簇**：{len(cluster_keys['_other'])} 张\n\n")

    lines.append("## 正文充实票（描述+评论 >80 字 · 宜优先人工核对）\n\n")
    for key, char_count, summary in substance[:40]:
        lines.append(
            f"- [{key}]({browse}/browse/{key})（{char_count} 字）{summary}\n"
        )
    if len(substance) > 40:
        lines.append(f"- … 另有 {len(substance) - 40} 张\n")

    lines.append("\n## 按父 Epic 聚簇（Top 10）\n\n")
    for parent, parent_keys in top_parents:
        if parent == "_orphan":
            label = "_orphan"
        elif parent in parent_idx:
            label = f"{parent} — {(parent_idx[parent].get('parent') or {}).get('summary', '')[:60]}"
        else:
            label = parent
        lines.append(f"### {label}（{len(parent_keys)}）\n\n")
        for ticket_key in sorted(parent_keys)[:15]:
            raw = raw_by_key.get(ticket_key, {})
            lines.append(f"- `{ticket_key}` · {raw.get('summary', '')[:72]}\n")
        if len(parent_keys) > 15:
            lines.append(f"- … +{len(parent_keys) - 15}\n")
        lines.append("\n")

    return "".join(lines)
