"""S1 facet keyword classification: title + body snippet → materialized relative path.

Maps Confluence pages into **facet-*** folders (keyword heuristics only — **not** proposition slugs).
See ``runtime.domain_knowledge_paths`` for naming SSOT.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = next(p for p in Path(__file__).resolve().parents if (p / "_install.py").is_file())
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
import _install

_install.bootstrap(__file__)

from typing import Sequence

from runtime.domain_knowledge_paths import (  # noqa: E402
    FACET_CHECKOUT,
    FACET_DIRS,
    FACET_UNMATCHED,
)
from runtime.domain_profiles import load_s1_facet_rules  # noqa: E402
from runtime.domain_profiles import load_s1_noise_rules  # noqa: E402
from runtime.classify_keywords import contains_classify_keyword
from wiki.lib.confluence_classify_utils import (  # noqa: E402
    facet_routing_kb_outline,
    facet_unmatched_kb_outline,
)

# (facet_folder, theme_label, keywords) — narrower facets first on tie-break.
_FACETS: tuple[tuple[str, str, Sequence[str]], ...] = load_s1_facet_rules()
_NOISE_RULES = load_s1_noise_rules()


def _explicit_noise_title(title: str) -> bool:
    t = title.strip()
    min_chars = int(_NOISE_RULES.get("min_title_chars") or 2)
    if len(t) < min_chars:
        return True
    if t in set(_NOISE_RULES.get("exact_titles") or ()):
        return True
    return any(t.startswith(prefix) for prefix in (_NOISE_RULES.get("title_prefixes") or ()))


def _score_facet(haystack_lc: str, haystack_raw: str, keywords: Sequence[str]) -> int:
    score = 0
    for kw in keywords:
        k = kw.strip()
        if not k:
            continue
        if k.isascii():
            low = k.lower()
            if contains_classify_keyword(haystack_lc, low):
                score += 1
        else:
            if k in haystack_raw:
                score += 1
    return score


def classify(title: str, body_snippet: str = "") -> tuple[str, str]:
    """
    Returns (theme_label, kb_outline). kb_outline ``—`` skips materialize for that page.

    Falls back to ``facet-unmatched/<slug>-<hash>.md`` when no keyword facet matches.
    """
    if _explicit_noise_title(title or ""):
        return ("显式噪声（仅抽取）", "—")

    title = title or ""
    raw = f"{title}\n{body_snippet or ''}"
    hay_lc = raw.lower()

    best_folder: str | None = None
    best_theme = ""
    best_score = 0

    for folder, theme, keywords in _FACETS:
        sc = _score_facet(hay_lc, raw, keywords)
        if sc > best_score:
            best_score = sc
            best_folder = folder
            best_theme = theme

    if best_folder is not None and best_score > 0:
        return (best_theme, facet_routing_kb_outline(best_folder, title))

    return (
        f"领域素材·待语义整理（未命中 facet → {FACET_UNMATCHED}）",
        facet_unmatched_kb_outline(title),
    )


__all__ = ["FACET_DIRS", "_FACETS", "classify"]
