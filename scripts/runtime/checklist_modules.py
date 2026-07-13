"""DOMAIN_MODULE_CHECKLIST.md parse/render (field blocks + legacy tables).

Canonical human format is one ``###`` module with indented field lines so narrow
viewports stay readable. Pipe tables remain accepted for older checklists.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from runtime.domain_knowledge_paths import (
    CHECKLIST_STATUS_PENDING,
    is_checklist_status_confirmed,
)

_DELIVER_SLUG_RE = re.compile(r"_deliver/([a-z0-9-]+)/")
_CHECKLIST_SLUG_RE = re.compile(r"（([^）]+)）")
_HEADING_RE = re.compile(r"^###\s+(.+?)\s*$")
_FIELD_RE = re.compile(
    r"^-\s+\*\*(?P<key>[^*]+)\*\*\s*[:：]\s*(?P<value>.*)$"
)

# Canonical field keys — English SSOT; Chinese aliases map to these in _KEY_ALIASES.
KEY_SLUG = "Proposition slug"
KEY_AXIS = "Strategy axis"
KEY_SCAN = "Domain subdirectory (scan)"
KEY_ENTRY = "Main entry"
KEY_STATUS = "Status"
KEY_GLOSS = "Glossary note"
KEY_NOTE = "Note"

_KEY_ALIASES: dict[str, str] = {
    # English variants
    "Proposition slug": KEY_SLUG,
    "proposition slug": KEY_SLUG,
    "slug": KEY_SLUG,
    "Strategy axis": KEY_AXIS,
    "strategy axis": KEY_AXIS,
    "Domain subdirectory (scan)": KEY_SCAN,
    "Main entry": KEY_ENTRY,
    "main entry": KEY_ENTRY,
    "Status": KEY_STATUS,
    "status": KEY_STATUS,
    "Glossary note": KEY_GLOSS,
    "glossary note": KEY_GLOSS,
    "Note": KEY_NOTE,
    "note": KEY_NOTE,
    # Chinese aliases (zh-CN deliverable locale)
    "命题 slug": KEY_SLUG,
    "strategy 维度": KEY_AXIS,
    "strategy": KEY_AXIS,
    "领域子目录（扫描）": KEY_SCAN,
    "扫描": KEY_SCAN,
    "主入口": KEY_ENTRY,
    "状态": KEY_STATUS,
    "术语备注": KEY_GLOSS,
    "备注": KEY_NOTE,
}


@dataclass(frozen=True)
class ChecklistModule:
    theme: str
    slug: str | None
    status: str
    main_entry: str = ""
    axis: str = ""
    scan_dirs: str = ""
    glossary_note: str = ""
    note: str = ""
    raw: str = ""


def _normalize_key(raw: str) -> str:
    return _KEY_ALIASES.get(raw.strip(), raw.strip())


def _slug_from_backticks(text: str) -> str | None:
    m = re.search(r"`([a-z0-9-]+)`", text)
    if not m:
        return None
    slug = m.group(1)
    if slug in ("—", "-") or slug.startswith("facet-") or slug.startswith("_"):
        return None
    return slug


def _slug_from_theme_or_entry(theme: str, main_entry: str, explicit: str | None = None) -> str | None:
    if explicit:
        cleaned = explicit.strip().strip("`").strip()
        if cleaned and cleaned not in ("—", "-", "–"):
            if cleaned.startswith("facet-"):
                cleaned = cleaned[6:]
            return cleaned
    m = _DELIVER_SLUG_RE.search(main_entry)
    if m:
        return m.group(1)
    matches = _CHECKLIST_SLUG_RE.findall(theme)
    if matches:
        return matches[-1].strip()
    return _slug_from_backticks(theme)


def _parse_field_blocks(text: str) -> list[ChecklistModule]:
    modules: list[ChecklistModule] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        hm = _HEADING_RE.match(lines[i].strip())
        if not hm:
            i += 1
            continue
        theme = hm.group(1).strip()
        # Skip non-module headings that happen to use ###
        if theme.startswith("文档") or theme in {"下一步", "门禁脚本", "溯源与附录"}:
            i += 1
            continue
        i += 1
        fields: dict[str, str] = {}
        block_lines = [hm.group(0)]
        while i < len(lines):
            raw = lines[i]
            stripped = raw.strip()
            if stripped.startswith("### "):
                break
            if stripped.startswith("## ") and not stripped.startswith("###"):
                break
            block_lines.append(raw)
            fm = _FIELD_RE.match(stripped)
            if fm:
                key = _normalize_key(fm.group("key"))
                fields[key] = fm.group("value").strip()
            i += 1
        status = fields.get(KEY_STATUS, "").strip()
        if not status:
            # Not a module card (no status field) — skip.
            continue
        main_entry = fields.get(KEY_ENTRY, "").strip().strip("`")
        explicit_slug = fields.get(KEY_SLUG)
        slug = _slug_from_theme_or_entry(theme, main_entry, explicit_slug)
        modules.append(
            ChecklistModule(
                theme=theme,
                slug=slug,
                status=status,
                main_entry=main_entry,
                axis=fields.get(KEY_AXIS, "").strip(),
                scan_dirs=fields.get(KEY_SCAN, "").strip(),
                glossary_note=fields.get(KEY_GLOSS, "").strip(),
                note=fields.get(KEY_NOTE, "").strip(),
                raw="\n".join(block_lines).strip(),
            )
        )
    return modules


def _table_has_proposition_slug(text: str) -> bool:
    return "命题 slug" in text


def _parse_legacy_tables(text: str) -> list[ChecklistModule]:
    modules: list[ChecklistModule] = []
    has_prop = _table_has_proposition_slug(text)
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if "------" in stripped or set(stripped.replace("|", "").strip()) <= {"-", " ", ":"}:
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) < 5:
            continue
        if cells[0] in {"主题", "工件", "脚本", "时机", "阶段"}:
            continue
        if "状态" in cells and "主题" in cells:
            continue
        if has_prop and len(cells) > 5:
            theme, prop_cell, axis, scan, entry, status = (
                cells[0],
                cells[1],
                cells[2],
                cells[3],
                cells[4],
                cells[5],
            )
            gloss = cells[6] if len(cells) > 6 else ""
            note = cells[7] if len(cells) > 7 else ""
            explicit = _slug_from_backticks(prop_cell) or prop_cell.strip("`")
        else:
            theme = cells[0]
            axis = cells[1] if len(cells) > 1 else ""
            scan = cells[2] if len(cells) > 2 else ""
            entry = cells[3] if len(cells) > 3 else ""
            status = cells[4] if len(cells) > 4 else ""
            gloss = cells[5] if len(cells) > 5 else ""
            note = cells[6] if len(cells) > 6 else ""
            explicit = None
        if not status:
            continue
        main_entry = entry.strip().strip("`")
        slug = _slug_from_theme_or_entry(theme, main_entry, explicit)
        modules.append(
            ChecklistModule(
                theme=theme,
                slug=slug,
                status=status,
                main_entry=main_entry,
                axis=axis,
                scan_dirs=scan,
                glossary_note=gloss,
                note=note,
                raw=stripped,
            )
        )
    return modules


def parse_checklist_modules(text: str) -> list[ChecklistModule]:
    """Parse modules; prefer field blocks when present, else legacy tables."""
    blocks = _parse_field_blocks(text)
    if blocks:
        return blocks
    return _parse_legacy_tables(text)


def parse_checklist_rows(text: str) -> list[tuple[str, str]]:
    """Compatibility: ``(theme_slug, status)`` for rows with a resolvable slug."""
    out: list[tuple[str, str]] = []
    for mod in parse_checklist_modules(text):
        if not mod.slug:
            continue
        out.append((mod.slug, mod.status))
    return out


def confirmed_slugs_from_checklist(text: str) -> list[str]:
    out: list[str] = []
    for mod in parse_checklist_modules(text):
        if not mod.slug or not is_checklist_status_confirmed(mod.status):
            continue
        out.append(mod.slug)
    return out


def confirmed_slug_theme_pairs(text: str) -> list[tuple[str, str]]:
    """``(slug, theme_cn)`` for confirmed modules."""
    out: list[tuple[str, str]] = []
    for mod in parse_checklist_modules(text):
        if not mod.slug or not is_checklist_status_confirmed(mod.status):
            continue
        theme_cn = mod.theme
        suffix = f"（{mod.slug}）"
        if theme_cn.endswith(suffix):
            theme_cn = theme_cn[: -len(suffix)].strip()
        out.append((mod.slug, theme_cn or mod.theme))
    return out


def statuses_by_slug(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for mod in parse_checklist_modules(text):
        if mod.slug:
            out[mod.slug] = mod.status
    return out


def has_pending_status(text: str) -> bool:
    from runtime.deliverable_locale import all_locale_values

    pending_tokens = set(all_locale_values("checklist.status_pending")) | {CHECKLIST_STATUS_PENDING, "pending"}
    for mod in parse_checklist_modules(text):
        raw = mod.status.strip()
        if any(tok and tok in raw for tok in pending_tokens):
            return True
        if raw.replace("*", "").strip().lower() == "pending":
            return True
    return False


def render_module_block(
    *,
    theme: str,
    slug: str | None,
    axis: str,
    scan_dirs: str,
    main_entry: str,
    status: str,
    glossary_note: str = "",
    note: str = "",
) -> list[str]:
    slug_display = f"`{slug}`" if slug else "—"
    entry = main_entry
    if entry and not entry.startswith("`") and entry != "—":
        entry = f"`{entry}`"
    return [
        f"### {theme}",
        f"- **{KEY_SLUG}**: {slug_display}",
        f"- **{KEY_AXIS}**: {axis}",
        f"- **{KEY_SCAN}**: {scan_dirs}",
        f"- **{KEY_ENTRY}**: {entry or '—'}",
        f"- **{KEY_STATUS}**: {status}",
        f"- **{KEY_GLOSS}**: {glossary_note}",
        f"- **{KEY_NOTE}**: {note}",
        "",
    ]


def render_checklist_header(root_id: str, *, purpose_lines: list[str] | None = None) -> list[str]:
    purpose = purpose_lines or [
        "Confirm S2 domain cuts, main entry, and Compose authorization (S3–S7).",
        "Narrow-screen friendly: **one block per module**; usually change only **Status** (`pending` → `confirmed`).",
        "Locale labels: `domain-knowledge/language/deliverable-locale-tokens.json`.",
    ]
    lines = [
        f"# 领域模块确认页 · 根 `{root_id}`",
        "",
        "## 文档用途",
    ]
    for p in purpose:
        lines.append(f"- {p}")
    lines.extend(
        [
            "",
            "## 必读主题",
            "",
            "「状态」= **`确认`** 才触发成稿。**`确认` ≠ 定稿已完成**。",
            "",
        ]
    )
    return lines
