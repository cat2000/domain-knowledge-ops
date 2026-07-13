#!/usr/bin/env python3
"""
Check curated Markdown for "domain-first" layout (no LLM).

Encourages the skeleton in domain-knowledge/distill-document-skeleton.md:
  - Reader-facing opening before heavy implementation sections
  - A dedicated business-rules section for non-Pass files

Pass stubs (## 非业务判定（Cursor） near top) are skipped.

Exit 1 if violations and not --warn-only.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_SCRIPTS = next(p for p in Path(__file__).resolve().parents if (p / "_install.py").is_file())
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
import _install

_install.bootstrap(__file__)
import _install

_install.bootstrap(__file__)

from distill._exclude import is_excluded, load_exclude_prefixes
from distill._paths import DISTILLED_BY_ROOT, PASS_MARKER, REPO_ROOT

# Headings that indicate "implementation / API" heavy sections (first occurrence wins for ordering)
IMPL_HEADING_RE = re.compile(
    r"^##\s+(实现与数据支撑|数据与接口|Gateway|接口与路径|技术实现|联调与字段)",
    re.IGNORECASE,
)

# Business substance sections
BUSINESS_HEADING_RE = re.compile(
    r"^##\s+(核心业务规则|业务规则|领域概述|文档用途|概述与范围)",
    re.IGNORECASE,
)

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check domain-first layout in curated (non-Pass files)."
    )
    parser.add_argument("--root-id", help="Only check this root page ID directory.")
    parser.add_argument(
        "--exclude-file",
        type=Path,
        default=None,
        metavar="PATH",
        help="Path prefix exclude file (same format as coverage script).",
    )
    parser.add_argument("--warn-only", action="store_true", help="Exit 0 even if violations.")
    parser.add_argument(
        "--min-bytes",
        type=int,
        default=400,
        help="Skip layout check for smaller files (bytes).",
    )
    args = parser.parse_args()

    if not DISTILLED_BY_ROOT.is_dir():
        print(f"Missing curated tree: {DISTILLED_BY_ROOT}", file=sys.stderr)
        return 0 if args.warn_only else 1

    exclude_prefixes: list[str] = []
    if args.exclude_file and args.exclude_file.is_file():
        exclude_prefixes = load_exclude_prefixes(args.exclude_file)

    violations: list[str] = []
    checked = 0
    skipped = 0

    for root_dir in sorted(DISTILLED_BY_ROOT.iterdir()):
        if not root_dir.is_dir():
            continue
        rid = root_dir.name
        if args.root_id and rid != args.root_id:
            continue
        for md in sorted(root_dir.rglob("*.md")):
            if md.name == "README.md":
                continue
            rel = md.relative_to(root_dir).as_posix()
            # Domain layout gate applies to deliver docs only.
            if not rel.startswith("_deliver/"):
                skipped += 1
                continue
            if md.name.endswith("命题清单.md"):
                skipped += 1
                continue
            if md.name.endswith("decision-atoms.md") or md.name.endswith("conflict-ledger.md"):
                skipped += 1
                continue
            if is_excluded(rel, exclude_prefixes):
                skipped += 1
                continue
            text = md.read_text(encoding="utf-8", errors="replace")
            if len(text.encode("utf-8")) < args.min_bytes:
                skipped += 1
                continue
            if is_pass_stub(text):
                skipped += 1
                continue

            checked += 1
            lines = text.splitlines()
            rel_repo = md.relative_to(REPO_ROOT)

            impl_idx = first_line_match_index(IMPL_HEADING_RE, lines)
            biz_idx = first_line_match_index(BUSINESS_HEADING_RE, lines)

            if biz_idx is None:
                violations.append(
                    f"{rel_repo}: missing a ## section like 「核心业务规则|业务规则|领域概述|文档用途|概述与范围」 "
                    f"(see domain-knowledge/distill-document-skeleton.md)"
                )

            if impl_idx is not None and biz_idx is not None and impl_idx < biz_idx:
                violations.append(
                    f"{rel_repo}: implementation section appears BEFORE business section "
                    f"(impl line ~{impl_idx + 1}, business ~{biz_idx + 1}); use domain-knowledge/distill-document-skeleton.md"
                )

            # Heuristic: crammed API paths in first 25 non-empty lines before any ##
            head_lines = [ln for ln in lines[:80] if ln.strip()]
            early_impl_density = sum(
                1
                for ln in head_lines[:25]
                if "/rest/" in ln or "/mvc/" in ln or "/ws/" in ln or "`/service/" in ln
            )
            if early_impl_density >= 6 and biz_idx is None:
                violations.append(
                    f"{rel_repo}: early fragment looks API-heavy ({early_impl_density} path-like lines) "
                    f"without a business-rules heading — likely integration notes, not domain KB"
                )

    if violations:
        print("Domain layout issues:", file=sys.stderr)
        for v in violations:
            print(f"  {v}", file=sys.stderr)

    print(
        f"Domain layout check: checked={checked} skipped_pass_or_small_or_excluded={skipped} "
        f"issues={len(violations)}"
    )

    if violations and not args.warn_only:
        return 1
    return 0
def is_pass_stub(text: str) -> bool:
    return PASS_MARKER in text[:8000]


def first_line_match_index(pattern: re.Pattern[str], lines: list[str]) -> int | None:
    for i, line in enumerate(lines):
        if pattern.match(line.strip()):
            return i
    return None




if __name__ == "__main__":
    sys.exit(main())
