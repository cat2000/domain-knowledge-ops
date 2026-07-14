"""
Proposition-first Jira distill tiers (no LLM).

Knowledge unit = 资格—分支—后果 命题簇, not one ticket.

distill_tier:
  proposition_core   — 须写入 Jira业务规则摘录 正文（代表票 + 分端索引）
  platform_variant   — 同命题分端实现，仅收录代表 KEY +  sibling 列表
  engineering_slice  — Gateway/埋点/映射；仅索引，不并入 _deliver
  cross_theme_ref    — 主命题在他域；本主题只留 KEY 引用
  index_only         — distill_queue 但薄/无 AC，仅遗漏扫描
"""

from __future__ import annotations

import re
from typing import Any, Mapping

# --- tier detection ---
_PLATFORM = re.compile(
    r"\[(ios|android|harmony|h5|iphone)\]",
    re.I,
)
_ENGINEERING = re.compile(
    r"\[gw\]|\[gateway\]|\bgateway\b|data tracking|sensor|埋点|"
    r"plexus|oracle to sql",
    re.I,
)
_CROSS_THEME_HINTS: dict[str, re.Pattern[str]] = {}

# Pack ships no tenant proposition tables. Put optional patterns in teams/<team>.json
# under "core_propositions" if a tenant needs keyword clustering.
CORE_PROPOSITIONS: dict[str, list[tuple[str, str, re.Pattern[str]]]] = {}


def propositions_for_theme(theme: str, root_id: str | None = None) -> list[tuple[str, str, re.Pattern[str]]]:
    """Theme → proposition patterns from team.json only (no pack-default tenant tables)."""
    team_key: str | None = None
    if root_id:
        try:
            from teams.registry import team_key_for_root_id

            team_key = team_key_for_root_id(str(root_id))
        except ImportError:
            team_key = None
    try:
        from jira.lib.jira_team_attribution import load_attribution_config

        cfg = load_attribution_config(team_key, root_id)
    except Exception:
        cfg = None
    if not cfg:
        return []
    raw_rows = (cfg.get("core_propositions") or {}).get(theme) or []
    out: list[tuple[str, str, re.Pattern[str]]] = []
    for row in raw_rows:
        if len(row) >= 3:
            out.append((str(row[0]), str(row[1]), re.compile(str(row[2]), re.I)))
    return out



def normalize_summary(summary: str) -> str:
    s = (summary or "").strip()
    s = re.sub(r"\[[^\]]+\]", " ", s)
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s[:100]


def proposition_cluster_id(
    primary: str,
    summary: str,
    parent_key: str | None,
    *,
    theme: str | None = None,
    root_id: str | None = None,
) -> str:
    """Stable cluster id for grouping platform duplicates."""
    norm = normalize_summary(summary)
    # match theme core pattern slug if any
    props = propositions_for_theme(theme, root_id) if theme else []
    if props:
        for slug, _, pat in props:
            if pat.search(norm) or pat.search(summary or ""):
                return f"{theme}:{slug}"
    base = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", norm)[:50].strip("-") or "misc"
    pk = parent_key or "orphan"
    return f"{primary}:{pk}:{base}"


def classify_distill_tier(
    raw: Mapping[str, Any],
    *,
    primary: str,
    themes: list[str],
    material_kind: str,
    distill_queue: bool,
    substance_tier: str,
    rule_like: bool,
) -> str:
    if not distill_queue:
        return "index_only"
    summary = raw.get("summary") or ""
    norm = normalize_summary(summary)
    blob = f"{summary}\n{raw.get('description_text') or ''}"


    if material_kind == "mapping_engineering" or _ENGINEERING.search(summary):
        return "engineering_slice"

    # cross-theme: primary not in theme slug but ticket tagged with theme
    for th in themes:
        if th == primary:
            continue
        pat = _CROSS_THEME_HINTS.get(th)
        if pat and pat.search(summary) and primary not in (th,):
            return "cross_theme_ref"

    if _PLATFORM.search(summary) and substance_tier != "rich":
        return "platform_variant"
    if _PLATFORM.search(summary):
        return "platform_variant"

    if substance_tier == "thin" and not rule_like:
        return "index_only"

    return "proposition_core"


def proposition_extract(tier: str) -> bool:
    return tier == "proposition_core"


def match_core_proposition(theme: str, summary: str, *, root_id: str | None = None) -> str | None:
    norm = normalize_summary(summary)
    for slug, _, pat in propositions_for_theme(theme, root_id):
        if pat.search(norm) or pat.search(summary or ""):
            return slug
    return None


def core_proposition_labels(theme: str, *, root_id: str | None = None) -> list[tuple[str, str]]:
    return [(s, label) for s, label, _ in propositions_for_theme(theme, root_id)]
