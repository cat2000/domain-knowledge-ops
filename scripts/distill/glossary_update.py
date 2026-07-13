#!/usr/bin/env python3
"""Update team glossary from S6 final draft term sections."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

_SCRIPTS = next(p for p in Path(__file__).resolve().parents if (p / "_install.py").is_file())
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
import _install

_install.bootstrap(__file__)

from runtime.domain_knowledge_paths import CURATED_BY_ROOT, DOMAIN_KNOWLEDGE  # noqa: E402

AUTO_SECTION_HEADING = "## 自动沉淀术语（S6 定稿）"
BEGIN_MARKER = "<!-- BEGIN AUTO-GLOSSARY: root={root_id} -->"
END_MARKER = "<!-- END AUTO-GLOSSARY: root={root_id} -->"
SECTION_HEADING_RE = re.compile(r"^##\s+", re.M)
TERM_LINE_RE = re.compile(r"^\s*-\s+`?(.+?)`?\s*[：:]\s*(.+?)\s*$")
CODE_SPAN_RE = re.compile(r"`([^`]+)`")


@dataclass
class GlossaryTerm:
    name: str
    definition: str
    sources: list[Path] = field(default_factory=list)


def extract_terms_from_final_draft(text: str, source: Path) -> list[GlossaryTerm]:
    terms_section = _section(text, "## 术语说明")
    if not terms_section.strip():
        return []

    terms: list[GlossaryTerm] = []
    for line in terms_section.splitlines():
        match = TERM_LINE_RE.match(line)
        if not match:
            continue
        name = _clean_term_name(match.group(1))
        definition = match.group(2).strip()
        if not name or not definition:
            continue
        terms.append(GlossaryTerm(name=name, definition=definition, sources=[source]))
    return terms


def collect_terms(root_id: str, *, curated_by_root: Path = CURATED_BY_ROOT) -> list[GlossaryTerm]:
    deliver_root = curated_by_root / str(root_id) / "_deliver"
    if not deliver_root.is_dir():
        return []

    merged: dict[str, GlossaryTerm] = {}
    for path in sorted(deliver_root.glob("*/*领域知识定稿.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        rel_source = path.relative_to(curated_by_root.parents[2])
        for term in extract_terms_from_final_draft(text, rel_source):
            key = _term_key(term.name)
            if key not in merged:
                merged[key] = term
            else:
                existing = merged[key]
                if term.definition not in existing.definition:
                    existing.definition = f"{existing.definition} / {term.definition}"
                existing.sources.extend(src for src in term.sources if src not in existing.sources)
    return sorted(merged.values(), key=lambda term: term.name.lower())


def render_auto_glossary_section(root_id: str, terms: list[GlossaryTerm]) -> str:
    lines = [
        BEGIN_MARKER.format(root_id=root_id),
        "",
        f"> 自动区由 `scripts/distill/glossary_update.py --root-id {root_id}` 从 S6 `## 术语说明` 生成。",
        "> 人工修订稳定后，可移动到上方团队分节；下次自动更新只替换本 root 区块。",
        "",
    ]
    if not terms:
        lines.append("> 当前 root 未发现 S6 术语说明。")
    for term in terms:
        lines.extend(
            [
                f"### {term.name}",
                "",
                f"- **定义**：{term.definition}",
                f"- **来源**：{', '.join(f'`{src.as_posix()}`' for src in term.sources)}",
                "",
            ]
        )
    lines.append(END_MARKER.format(root_id=root_id))
    lines.append("")
    return "\n".join(lines)


def update_glossary_text(existing: str, root_id: str, root_section: str) -> str:
    begin = BEGIN_MARKER.format(root_id=root_id)
    end = END_MARKER.format(root_id=root_id)
    block_re = re.compile(re.escape(begin) + r".*?" + re.escape(end) + r"\n?", re.S)
    if block_re.search(existing):
        return block_re.sub(root_section, existing)

    if AUTO_SECTION_HEADING not in existing:
        base = existing.rstrip()
        return f"{base}\n\n---\n\n{AUTO_SECTION_HEADING}\n\n{root_section}"

    insert_at = existing.find(AUTO_SECTION_HEADING) + len(AUTO_SECTION_HEADING)
    return f"{existing[:insert_at].rstrip()}\n\n{root_section}{existing[insert_at:].lstrip()}"


def update_glossary_file(
    *,
    root_id: str,
    curated_by_root: Path = CURATED_BY_ROOT,
    glossary_path: Path = DOMAIN_KNOWLEDGE / "language" / "glossary.md",
) -> bool:
    terms = collect_terms(root_id, curated_by_root=curated_by_root)
    section = render_auto_glossary_section(root_id, terms)
    existing = glossary_path.read_text(encoding="utf-8") if glossary_path.is_file() else "# 术语表\n"
    updated = update_glossary_text(existing, root_id, section)
    if updated == existing:
        return False
    glossary_path.parent.mkdir(parents=True, exist_ok=True)
    glossary_path.write_text(updated, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Update glossary.md from S6 final draft terms.")
    parser.add_argument("--root-id", required=True, help="Confluence storage root id")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Do not write; fail if glossary.md would change.",
    )
    args = parser.parse_args()

    glossary_path = DOMAIN_KNOWLEDGE / "language" / "glossary.md"
    terms = collect_terms(args.root_id)
    section = render_auto_glossary_section(args.root_id, terms)
    existing = glossary_path.read_text(encoding="utf-8") if glossary_path.is_file() else "# 术语表\n"
    updated = update_glossary_text(existing, args.root_id, section)
    if args.check:
        if updated != existing:
            print(f"glossary_update: {glossary_path} is stale for root_id={args.root_id}", file=sys.stderr)
            return 1
        print(f"glossary_update: {glossary_path} is up to date for root_id={args.root_id}")
        return 0

    if updated != existing:
        glossary_path.parent.mkdir(parents=True, exist_ok=True)
        glossary_path.write_text(updated, encoding="utf-8")
        print(f"glossary_update: updated {glossary_path} from {len(terms)} terms")
    else:
        print(f"glossary_update: no changes for {glossary_path}")
    return 0


def _section(text: str, heading: str) -> str:
    if heading not in text:
        return ""
    after = text.split(heading, 1)[1]
    next_heading = SECTION_HEADING_RE.search(after)
    if next_heading:
        return after[: next_heading.start()]
    return after


def _clean_term_name(value: str) -> str:
    value = value.strip()
    code_match = CODE_SPAN_RE.fullmatch(value)
    if code_match:
        return code_match.group(1).strip()
    return value.strip("` ")


def _term_key(value: str) -> str:
    return re.sub(r"\s+", " ", value).casefold()


if __name__ == "__main__":
    raise SystemExit(main())
