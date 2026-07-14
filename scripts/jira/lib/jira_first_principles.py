"""
First-principles Jira ticket attribution (no LLM).

Separates:
  - business proposition → primary / themes (checklist + teams/<team>.json only)
  - product channel → product_line label (never a domain module)
  - material kind → normative_business | mapping_engineering | collaboration_noise

Themes and keyword facets are **not** hard-coded for any tenant in this pack.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from runtime.classify_keywords import contains_classify_keyword

from jira.lib.jira_proposition import classify_distill_tier, proposition_cluster_id
from jira.lib.jira_proposition import proposition_extract as should_proposition_extract_body
from jira.lib.jira_substance import should_distill_queue, substance_metrics

# Pack ships no tenant theme set. Themes come from checklist + teams/<team>.json.
# (Historical name kept as empty alias so old imports fail closed.)
DEFAULT_CMA_THEMES: frozenset[str] = frozenset()

# Keyword facets live in teams/<team>.json — not in this pack module.
_PROPOSITION_FACETS: tuple[tuple[str, Sequence[str]], ...] = ()

_COLLABORATION_NOISE = re.compile(
    r"release work transfer|code transfer|code review with 3pl|merge code for|"
    r"save for late function discovery|support 3pl|perpare the code transfer|"
    r"auto update the android version$",
    re.I,
)

_ENGINEERING_ONLY = re.compile(
    r"\beslint\b|editorconf|console log for splunk|add appdynamics|"
    r"technical design$|define schema|poc for",
    re.I,
)

# Optional channel labels only (never become primary domain slugs).
# Prefer teams/<team>.json product_line patterns when present; these are generic fallbacks.
_PRODUCT_LINE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("gateway", re.compile(r"\bgateway\b|\[gw\]", re.I)),
    (
        "wechat",
        re.compile(r"\[wechat\]|wechat|mini\s*program|miniprogram|小程序", re.I),
    ),
)


@dataclass(frozen=True)
class AttributionResult:
    key: str
    type: str
    parent: str | None
    hierarchy_root: str | None
    parent_summary: str | None
    themes: list[str]
    primary: str
    product_line: str
    material_kind: str
    signal: str
    confidence: str
    effective_at: str
    business_extract: bool
    distill_queue: bool
    distill_tier: str
    proposition_id: str
    proposition_extract: bool
    substance_chars: int
    substance_tier: str
    wiki_gap: bool
    spike_role: str | None
    related_keys: list[str]
    comment_count: int
    one_line: str
    attribution_method: str = "first_principles"
    attribution_notes: str | None = None


def _haystack(raw: Mapping[str, Any]) -> tuple[str, str]:
    parts = [
        raw.get("summary") or "",
        raw.get("description_text") or "",
        " ".join(raw.get("labels") or []),
    ]
    parent = raw.get("parent") or {}
    if isinstance(parent, dict):
        parts.append(parent.get("summary") or "")
    raw_s = "\n".join(parts)
    return raw_s, raw_s.lower()


def detect_product_line(raw_s: str) -> str:
    hits = [name for name, pat in _PRODUCT_LINE_PATTERNS if pat.search(raw_s)]
    if "mall" in hits and "hui" in hits:
        return "shared"
    if len(hits) == 1:
        return hits[0]
    if "gateway" in hits and len(hits) >= 2:
        return hits[0] if hits[0] != "gateway" else "gateway"
    if hits:
        return hits[0]
    return "unknown"


def _score_facet(hay_lc: str, hay_raw: str, keywords: Sequence[str]) -> int:
    score = 0
    for kw in keywords:
        k = kw.strip()
        if not k:
            continue
        if k.isascii():
            if contains_classify_keyword(hay_lc, k.lower()):
                score += 1
        elif k in hay_raw:
            score += 1
    return score


def score_propositions(
    raw: Mapping[str, Any],
    *,
    facets: tuple[tuple[str, Sequence[str]], ...] | None = None,
) -> list[tuple[str, int]]:
    hay_raw, hay_lc = _haystack(raw)
    table = facets if facets is not None else ()
    scored: list[tuple[str, int]] = []
    for slug, keywords in table:
        sc = _score_facet(hay_lc, hay_raw, keywords)
        if sc > 0:
            scored.append((slug, sc))
    scored.sort(key=lambda x: (-x[1], x[0]))
    return scored


def _related_keys(raw: Mapping[str, Any], key: str) -> list[str]:
    hay_raw, _ = _haystack(raw)
    found: list[str] = []
    for m in re.finditer(r"DEV-\d+", hay_raw):
        rk = m.group(0)
        if rk != key and rk not in found:
            found.append(rk)
    return found[:8]


def effective_at(raw: Mapping[str, Any]) -> str:
    updated = raw.get("updated") or ""
    comments = raw.get("comments") or []
    if comments:
        last = max((c.get("created") or "") for c in comments)
        return last if last > updated else updated
    return updated


def classify_ticket(
    raw: Mapping[str, Any],
    *,
    allowed_themes: frozenset[str] | None = None,
    parent_raw: Mapping[str, Any] | None = None,
    team_key: str | None = None,
    root_id: str | None = None,
) -> AttributionResult:
    """Classify one ticket from fetch_jira_tickets raw JSON."""
    from jira.lib.jira_checklist_themes import load_allowed_themes
    from jira.lib.jira_team_attribution import (
        facets_tuple,
        load_attribution_config,
        normative_primaries,
        resolve_primary_hints,
        sink_slugs,
    )

    cfg = load_attribution_config(team_key, root_id)
    rid = root_id or (str(cfg.get("root_id")) if cfg else None)
    from jira.lib.jira_checklist_themes import FALLBACK_THEMES

    allowed = allowed_themes or (
        load_allowed_themes(rid) if rid else frozenset(FALLBACK_THEMES)
    )
    facet_table = facets_tuple(cfg)
    normative = normative_primaries(cfg, rid) if rid else frozenset()
    sinks = sink_slugs(cfg)
    key = str(raw.get("key") or "")
    itype = str(raw.get("issuetype") or "Story")
    parent_key = raw.get("parent_key")
    parent = raw.get("parent") or {}
    parent_summary = parent.get("summary") if isinstance(parent, dict) else None
    hroot = raw.get("hierarchy_root_key")
    comments = raw.get("comments") or []
    nc = len(comments)
    summary = (raw.get("summary") or "").strip()
    hay_raw, hay_lc = _haystack(raw)
    product_line = detect_product_line(hay_raw)
    hinted = None

    # --- material kind ---
    sub = substance_metrics(raw)
    substance_chars = int(sub["substance_chars"])
    substance_tier = str(sub["substance_tier"])

    if _COLLABORATION_NOISE.search(hay_raw):
        material_kind = "collaboration_noise"
        signal = "pass"
        primary = "requirements"
        themes = ["requirements"]
        business_extract = False
        distill_queue = False
        distill_tier = "index_only"
        proposition_id = proposition_cluster_id(primary, summary, parent_key)
        proposition_extract = False
        wiki_gap = False
        confidence = "medium"
        one_line = summary[:120] or "协作/移交/占位类票"
    else:
        hinted = resolve_primary_hints(raw, cfg)
        scored = score_propositions(raw, facets=facet_table)
        if not scored and parent_raw:
            scored = score_propositions(parent_raw, facets=facet_table)

        if hinted and hinted in allowed:
            primary = hinted
            themes = [hinted] + [slug for slug, _ in scored[:3] if slug in allowed and slug != hinted]
        elif scored:
            primary = scored[0][0]
            themes = [slug for slug, _ in scored[:3] if slug in allowed]
            if primary not in themes:
                themes.insert(0, primary)
        else:
            primary = "requirements"
            themes = ["requirements"]

        if _ENGINEERING_ONLY.search(hay_raw) and not re.search(
            r"bug|defect|production", hay_raw, re.I
        ):
            material_kind = "mapping_engineering"
            signal = "engineering"
            business_extract = False
            wiki_gap = False
            confidence = "medium"
        elif itype == "Spike":
            material_kind = "mapping_engineering"
            signal = "engineering"
            business_extract = False
            wiki_gap = primary in normative
            confidence = "medium"
        elif itype in ("Bug", "Defect") or "bug" in (raw.get("issuetype") or "").lower():
            material_kind = "normative_business"
            signal = "business"
            business_extract = True
            wiki_gap = True
            confidence = "medium"
        elif primary in normative:
            material_kind = "normative_business"
            signal = "business" if nc >= 1 else "engineering"
            business_extract = signal == "business"
            wiki_gap = True
            confidence = "medium" if nc >= 1 else "low"
        elif primary in sinks:
            material_kind = "mapping_engineering"
            signal = "engineering"
            business_extract = False
            wiki_gap = False
            confidence = "medium"
        else:
            material_kind = "mapping_engineering"
            signal = "engineering" if nc > 0 else "pass"
            business_extract = False
            wiki_gap = False
            confidence = "low"

        one_line = summary[:120]

    spike_role = "feasibility" if itype == "Spike" else None

    if material_kind != "collaboration_noise":
        distill_queue = should_distill_queue(
            raw, material_kind=material_kind, issuetype=itype
        )
        business_extract = distill_queue

    theme_for_prop = next(
        (t for t in themes if t in allowed and t not in sinks),
        primary,
    )
    distill_tier = classify_distill_tier(
        raw,
        primary=primary,
        themes=themes,
        material_kind=material_kind,
        distill_queue=distill_queue,
        substance_tier=substance_tier,
        rule_like=bool(sub.get("rule_like")),
    )
    proposition_id = proposition_cluster_id(
        primary,
        summary,
        parent_key,
        theme=theme_for_prop if theme_for_prop in allowed else None,
        root_id=rid,
    )
    proposition_extract = should_proposition_extract_body(distill_tier)

    # Channel / filing-layout slugs must not become primary (see FORBIDDEN_THEME_SLUGS).
    from jira.lib.pipeline_check_logic import FORBIDDEN_THEME_SLUGS

    for bad in FORBIDDEN_THEME_SLUGS:
        if primary == bad:
            primary = "requirements"
            themes = ["requirements"]
            break

    if primary not in allowed:
        primary = "requirements"
        if "requirements" not in themes:
            themes = ["requirements"] + [t for t in themes if t in allowed]

    # 业务命题不得落在 sink 桶（分诊用，非 _deliver 主题）
    if primary in sinks and hinted and hinted in allowed:
        primary = hinted
        themes = [hinted] + [t for t in themes if t != hinted and t in allowed]

    return AttributionResult(
        key=key,
        type=itype,
        parent=parent_key,
        hierarchy_root=hroot,
        parent_summary=parent_summary,
        themes=themes,
        primary=primary,
        product_line=product_line,
        material_kind=material_kind,
        signal=signal,
        confidence=confidence,
        effective_at=effective_at(raw),
        business_extract=business_extract,
        distill_queue=distill_queue,
        distill_tier=distill_tier,
        proposition_id=proposition_id,
        proposition_extract=proposition_extract,
        substance_chars=substance_chars,
        substance_tier=substance_tier,
        wiki_gap=wiki_gap,
        spike_role=spike_role,
        related_keys=_related_keys(raw, key),
        comment_count=nc,
        one_line=one_line,
        attribution_method="first_principles",
        attribution_notes=None,
    )
