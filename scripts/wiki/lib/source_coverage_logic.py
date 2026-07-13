"""Pure helpers for source-coverage.md rendering (no dynamic imports)."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from wiki.lib.confluence_kb_zh_display import parse_title_from_extract_file
from wiki.lib.confluence_classify_utils import call_classify, read_extract_md_body


def title_for_table(pages_dir: Optional[Path], page_id: str, api_title: str) -> str:
    """Prefer localized title from extract front matter when pages-dir is set."""
    if pages_dir:
        extract_path = pages_dir / f"{page_id}.md"
        if extract_path.is_file():
            title = parse_title_from_extract_file(extract_path.read_text(encoding="utf-8"))
            if title:
                return title
    return api_title


def body_snippet_for_page(pages_dir: Optional[Path], page_id: str) -> str:
    if pages_dir is None:
        return ""
    return read_extract_md_body(pages_dir / f"{page_id}.md")


def render_source_coverage_markdown(
    rows: list[dict],
    *,
    classify: Callable[[str, str], tuple[str, str]],
    root_page_id: str,
    root_url: str,
    root_label: str,
    pages_dir: Optional[Path] = None,
) -> str:
    row_count = len(rows)
    label = root_label.strip() or f"Root {root_page_id}"
    sorted_rows = sorted(rows, key=lambda row: int(row["id"]))

    title_doc = (
        f"# Confluence 子树 · 来源页索引（根页 `{root_page_id}` · **facet_classify**）"
    )
    intro = (
        "**领域 KB 落点**由 `facet_classify.py`（`strategy.md` 模板维度 + 正文摘要）决定；"
        "未命中维度时落在 **`facet-unmatched/`**。正文见 [`./pages/`](./pages/)。"
    )

    lines = [
        title_doc,
        "",
        f"> **自动生成**：`scripts/sync_domain_knowledge_from_confluence.py` · 根页：[{label}]({root_url})",
        "",
        intro,
        "",
        "| # | 主题 | 领域 KB 落点 | 页面标题 | Page ID |",
        "|---|------|----------------|----------|---------|",
    ]
    for index, row in enumerate(sorted_rows, start=1):
        page_id = str(row["id"])
        title = row.get("title") or ""
        link = row.get("webUi") or ""
        snippet = body_snippet_for_page(pages_dir, page_id)
        theme, kb = call_classify(classify, title, snippet)
        display_title = title_for_table(pages_dir, page_id, title)
        title_cell = f"[{display_title}]({link})" if link else display_title
        kb_cell = f"`{kb}`" if kb != "—" else "—"
        lines.append(f"| {index} | {theme} | {kb_cell} | {title_cell} | `{page_id}` |")
    lines.append("")
    lines.append(
        f"共 **{row_count}** 页（含枚举根页；清单 [`./descendants-full.json`](./descendants-full.json)）。"
    )
    lines.append("")
    return "\n".join(lines) + "\n"
