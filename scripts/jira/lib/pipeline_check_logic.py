"""Pure validation rules for Jira pipeline artifacts (no I/O)."""

from __future__ import annotations

FORBIDDEN_THEME_SLUGS = frozenset({"mall-app", "hui-app", "mall", "hui", "promotool"})


def issues_for_raw_ticket(key: str, doc: dict | None, raw_exists: bool) -> list[str]:
    if not raw_exists or doc is None:
        return [f"missing raw/{key}.json"]
    issues: list[str] = []
    if "description_text" not in doc:
        issues.append(f"{key}: no description_text in raw")
    if doc.get("comments") is None:
        issues.append(f"{key}: no comments array in raw")
    return issues


def issues_for_attribution(
    key: str,
    meta: dict,
    *,
    allowed: set[str],
) -> list[str]:
    issues: list[str] = []
    primary = meta.get("primary")
    themes = meta.get("themes") or []
    if isinstance(themes, str):
        themes = [themes]
    if primary in FORBIDDEN_THEME_SLUGS:
        issues.append(f"{key}: primary must not be product channel ({primary})")
    for theme in themes:
        if theme in FORBIDDEN_THEME_SLUGS:
            issues.append(f"{key}: themes must not use product channel slug ({theme})")
    if primary and primary not in allowed:
        issues.append(f"{key}: primary {primary!r} not in checklist themes")
    for theme in themes:
        if theme not in allowed:
            issues.append(f"{key}: theme {theme!r} not in checklist themes")
    if not meta.get("product_line"):
        issues.append(f"{key}: missing product_line")
    if not meta.get("material_kind"):
        issues.append(f"{key}: missing material_kind")
    if meta.get("substance_tier") is None and "substance_chars" not in meta:
        issues.append(f"{key}: missing substance_tier (re-run attribute_jira_tickets.py)")
    if not meta.get("distill_tier"):
        issues.append(f"{key}: missing distill_tier (re-run attribute_jira_tickets.py)")
    return issues
