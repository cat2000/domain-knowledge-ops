"""Shared helpers: body snippet shaping and calling classify with optional 2nd argument."""

from __future__ import annotations

import hashlib
import inspect
import re
from typing import Any, Callable, Tuple


def _slug_hash_segment(title: str) -> tuple[str, str]:
    """Stable slug + short hash from page title (shared by routing helpers)."""
    h = hashlib.sha256(title.encode("utf-8")).hexdigest()[:10]
    s = re.sub(r"[\s/\\]+", "-", title.strip())
    s = re.sub(r"[^\w\u4e00-\u9fff\u3000-\u303f-]+", "", s)
    s = s.strip("-")[:44] or "untitled"
    return s, h


def facet_unmatched_kb_outline(title: str) -> str:
    """Stable ``facet-unmatched/<slug>-<hash>.md`` (S1 fallback when no keyword facet matches)."""
    s, h = _slug_hash_segment(title)
    return f"facet-unmatched/{s}-{h}.md"


def facet_routing_kb_outline(facet_dir: str, title: str) -> str:
    """Per-page path under a facet folder: ``<facet_dir>/<slug>-<hash>.md`` (one Confluence page → one file)."""
    s, h = _slug_hash_segment(title)
    d = facet_dir.strip().strip("/").replace("\\", "/")
    return f"{d}/{s}-{h}.md"


from runtime.classify_keywords import contains_classify_keyword
# Bound total text passed to keyword heuristics (title + body already separate).
DEFAULT_SNIPPET_MAX = 8000


def normalize_body_snippet(text: str, max_chars: int = DEFAULT_SNIPPET_MAX) -> str:
    """Collapse whitespace; keep enough text for domain keyword hits."""
    s = (text or "").strip()
    s = re.sub(r"[\r\n\t]+", " ", s)
    s = re.sub(r" +", " ", s).strip()
    if len(s) > max_chars:
        s = s[:max_chars]
    return s


def call_classify(
    classify_fn: Callable[..., Tuple[str, str]],
    title: str,
    body_plain: str = "",
) -> Tuple[str, str]:
    """Call classify(title) or classify(title, snippet) depending on the module signature."""
    snippet = normalize_body_snippet(body_plain) if body_plain else ""
    try:
        sig = inspect.signature(classify_fn)
        params = [
            p
            for p in sig.parameters.values()
            if p.kind
            in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            )
        ]
        if len(params) >= 2:
            return classify_fn(title, snippet)
    except (TypeError, ValueError):
        pass
    return classify_fn(title)


def should_apply_body_heuristic(theme: str, kb: str) -> bool:
    """When title-only classification is weak, allow a second pass on body text."""
    if "待核对" in theme:
        return True
    if "噪声" in theme or "占位" in theme:
        return False
    if "非业务深耕" in theme:
        return False
    if kb != "—":
        return False
    return True


def read_extract_md_body(path: Any, max_chars: int = DEFAULT_SNIPPET_MAX) -> str:
    """Return markdown body after YAML front matter for snippet extraction."""
    from pathlib import Path

    p = Path(path)
    if not p.is_file():
        return ""
    raw = p.read_text(encoding="utf-8")
    if raw.startswith("---\n"):
        end = raw.find("\n---\n", 4)
        if end != -1:
            raw = raw[end + 5 :]
    return normalize_body_snippet(raw, max_chars=max_chars)
