"""Pure helpers for Jira ticket attribution YAML (no LLM)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from jira.lib.attribution_yaml import parse_attribution_yaml
from jira.lib.jira_first_principles import AttributionResult


def yaml_quote(val) -> str:
    if val is None:
        return "null"
    if isinstance(val, bool):
        return "true" if val else "false"
    text = str(val)
    if not text:
        return '""'
    if any(c in text for c in ":{}[]#&*!|>\'\"") or text.strip() != text:
        return json.dumps(text, ensure_ascii=False)
    return text


def should_preserve_attr(attr_path: Path) -> bool:
    """Keep only explicit Cursor reviews that already satisfy schema v2."""
    if not attr_path.is_file():
        return False
    text = attr_path.read_text(encoding="utf-8")
    if "attribution_method: cursor_review" not in text:
        return False
    return "product_line:" in text and "material_kind:" in text


def result_to_yaml(result: AttributionResult, scanned_at: str) -> str:
    lines = [
        f"key: {result.key}",
        f"type: {result.type}",
        f"parent: {yaml_quote(result.parent)}",
        f"hierarchy_root: {yaml_quote(result.hierarchy_root)}",
        f"parent_summary: {yaml_quote(result.parent_summary)}",
        "themes:",
    ]
    for theme in result.themes:
        lines.append(f"  - {theme}")
    lines.extend(
        [
            f"primary: {result.primary}",
            f"product_line: {result.product_line}",
            f"material_kind: {result.material_kind}",
            f"signal: {result.signal}",
            f"confidence: {result.confidence}",
            f"substance_chars: {result.substance_chars}",
            f"substance_tier: {result.substance_tier}",
            f"distill_queue: {'true' if result.distill_queue else 'false'}",
            f"distill_tier: {result.distill_tier}",
            f"proposition_id: {yaml_quote(result.proposition_id)}",
            f"proposition_extract: {'true' if result.proposition_extract else 'false'}",
            f"effective_at: {yaml_quote(result.effective_at)}",
            f"scanned_at: {yaml_quote(scanned_at)}",
            f"attribution_method: {result.attribution_method}",
            "supersedes: []",
            "amended_by: []",
            "related_keys:",
        ]
    )
    for related_key in result.related_keys:
        lines.append(f"  - {related_key}")
    if not result.related_keys:
        lines[-1] = "related_keys: []"
    lines.extend(
        [
            f"comment_count: {result.comment_count}",
            f"wiki_gap: {'true' if result.wiki_gap else 'false'}",
            f"spike_role: {yaml_quote(result.spike_role)}",
            f"business_extract: {'true' if result.business_extract else 'false'}",
            f"one_line: {yaml_quote(result.one_line)}",
        ]
    )
    if result.attribution_notes:
        lines.append(f"attribution_notes: {yaml_quote(result.attribution_notes)}")
    return "\n".join(lines) + "\n"


def rebuild_index(jira_dir: Path, team: str, root_id: str) -> dict:
    import json as json_mod

    tickets: dict = {}
    theme_hits: dict[str, int] = {}
    product_line_hits: dict[str, int] = {}
    attr_dir = jira_dir / "attribution"

    for path in sorted(attr_dir.glob("*.yaml")):
        record = {"key": path.stem, **parse_attribution_yaml(path.read_text(encoding="utf-8"))}
        ticket_key = str(record.get("key", path.stem))
        themes = record.get("themes") or []
        if isinstance(themes, str):
            themes = [themes]
        product_line = record.get("product_line") or "unknown"
        tickets[ticket_key] = {
            "themes": themes,
            "primary": record.get("primary"),
            "product_line": product_line,
            "material_kind": record.get("material_kind"),
            "signal": record.get("signal"),
            "substance_chars": record.get("substance_chars"),
            "substance_tier": record.get("substance_tier"),
            "distill_queue": bool(record.get("distill_queue")),
            "distill_tier": record.get("distill_tier") or "index_only",
            "proposition_id": record.get("proposition_id"),
            "proposition_extract": bool(record.get("proposition_extract")),
            "business_extract": bool(record.get("business_extract")),
            "one_line": record.get("one_line"),
            "parent": record.get("parent"),
        }
        for theme in themes:
            theme_hits[theme] = theme_hits.get(theme, 0) + 1
        product_line_hits[product_line] = product_line_hits.get(product_line, 0) + 1

    index_doc = {
        "root_id": root_id,
        "team": team,
        "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "mode": "first_principles",
        "attribution_model": "domain-knowledge/jira/first-principles-attribution.md",
        "pipeline_design": "domain-knowledge/jira/pipeline-design.md",
        "ticket_count": len(tickets),
        "distill_queue_count": sum(1 for ticket in tickets.values() if ticket.get("distill_queue")),
        "proposition_extract_count": sum(
            1 for ticket in tickets.values() if ticket.get("proposition_extract")
        ),
        "theme_hits": dict(sorted(theme_hits.items(), key=lambda item: -item[1])),
        "product_line_hits": dict(sorted(product_line_hits.items(), key=lambda item: -item[1])),
        "tickets": tickets,
    }
    (jira_dir / "_ticket_attribution.json").write_text(
        json_mod.dumps(index_doc, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return index_doc
