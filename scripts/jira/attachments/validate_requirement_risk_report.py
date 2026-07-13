#!/usr/bin/env python3
"""
Validate a requirement_risk-style Markdown report for internal consistency.

Severity labels: Chinese (必须修复/应当澄清/可选) or English (MUST FIX/SHOULD CLARIFY/OPTIONAL),
selected via --lang (or env REQUIREMENT_RISK_LANG).

1) Count severities from FULL_UNKNOWN_MAP-style headings: #### R-00N · <severity> · …
2) If a summary counts line exists, compare to (1)
3) Optional Top section vs MUST rows (when total MUST <=5)
4) Optional term-lint (zh only) and --evidence-dir, R-001↔R-002 hint

Exit 0 if OK, 1 if mismatch.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

__version__ = "1.3.0"

# ---------------------------------------------------------------------------
# Locale: add / edit display strings in STRINGS[lang] only; regexes in LocaleSpec
# ---------------------------------------------------------------------------


class LocaleSpec(Protocol):
    must: str
    should: str
    optional: str
    heading_re: re.Pattern[str]
    counts_re: re.Pattern[str]
    top_starts: tuple[str, ...]
    top_block_end_markers: tuple[str, ...]


@dataclass(frozen=True)
class _ZhLocale:
    must: str = "必须修复"
    should: str = "应当澄清"
    optional: str = "可选"
    heading_re: re.Pattern[str] = re.compile(
        r"^####\s+(R-\d+)\s+·\s*(必须修复|应当澄清|可选)\s*·", re.MULTILINE
    )
    counts_re: re.Pattern[str] = re.compile(
        r"(?:\*\*)?计数(?:\*\*)?\s*[:：]\s*必须修复\s*(\d+)\s*[·/／]\s*应当澄清\s*(\d+)\s*[·/／]\s*可选\s*(\d+)"
    )
    top_starts: tuple[str, ...] = ("必须修复 Top", "MUST-FIX top", "MUST-FIX Top")
    top_block_end_markers: tuple[str, ...] = (
        "\n### `FULL_UNKNOWN_MAP`",
        "\n### 完整风险清单",
        "\n### `PRIORITIZED_BLOCKERS`",
        "\n### `AUDIT_COUNTS`",
        "\n## Layer 2",
        "\n- 计数：",
        "\n计数：",
        "\n**计数**",
    )


@dataclass(frozen=True)
class _EnLocale:
    must: str = "MUST FIX"
    should: str = "SHOULD CLARIFY"
    optional: str = "OPTIONAL"
    # Allow middle dot or hyphen variants (avoid requiring exact Unicode)
    heading_re: re.Pattern[str] = re.compile(
        r"^####\s+(R-\d+)\s*·\s*(MUST FIX|SHOULD CLARIFY|OPTIONAL)\s*·", re.MULTILINE
    )
    counts_re: re.Pattern[str] = re.compile(
        r"Counts\s*:\s*MUST\s*(\d+)\s*[·/／]\s*SHOULD\s*(\d+)\s*[·/／]\s*OPTIONAL\s*(\d+)",
        re.IGNORECASE,
    )
    top_starts: tuple[str, ...] = ("MUST-FIX Top", "MUST FIX Top", "必须修复 Top")
    top_block_end_markers: tuple[str, ...] = (
        "\n### `FULL_UNKNOWN_MAP`",
        "\n### `PRIORITIZED_BLOCKERS`",
        "\n### `AUDIT_COUNTS`",
        "\n## Layer 2",
        "\n- Counts:",
        "\nCounts:",
        "\n- 计数：",
        "\n计数：",
    )

def main() -> int:
    default_lang = (os.environ.get("REQUIREMENT_RISK_LANG") or "zh").strip().lower()[:2] or "zh"
    if default_lang not in ("zh", "en"):
        default_lang = "zh"

    parser = argparse.ArgumentParser(
        description=_S(default_lang).get("ap_description", "validate requirement_risk")
    )
    parser.add_argument("path", nargs="?", help="Markdown file (default: stdin)")
    parser.add_argument("-q", "--quiet", action="store_true")
    t0 = _S(default_lang)
    parser.add_argument("--evidence-dir", metavar="DIR", type=Path, help=str(t0.get("help_evidence_dir")))
    parser.add_argument("--strict", action="store_true", help=str(t0.get("help_strict")))
    parser.add_argument("--no-term-lint", action="store_true", help=str(t0.get("help_no_term_lint")))
    parser.add_argument("--no-r001r002-hint", action="store_true", help=str(t0.get("help_no_r001r2")))
    parser.add_argument(
        "--brief",
        action="store_true",
        help="Brief mode: require 范围 + 计数 + EVIDENCE_COVERAGE; R headings optional.",
    )
    parser.add_argument(
        "--lang",
        default=os.environ.get("REQUIREMENT_RISK_LANG", "zh"),
        help=str(t0.get("help_lang")),
    )
    args = parser.parse_args()
    try:
        loc = _get_locale(args.lang)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1
    lang = "en" if loc.must == "MUST FIX" else "zh"
    table = _S(lang)

    if args.path:
        with open(args.path, encoding="utf-8") as f:
            text = f.read()
    else:
        text = sys.stdin.read()

    if not text.strip():
        print(_msg(table, "empty_input"), file=sys.stderr)
        return 1

    errors: list[str] = []
    warnings: list[str] = []

    errors.extend(check_presentation_basics(text, brief=args.brief, table=table))

    try:
        by_id = parse_heading_severities(text, loc, table)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1

    if not by_id and not args.brief:
        if not args.quiet:
            print(_msg(table, "no_headings"), file=sys.stderr)
        return 1

    if not args.no_term_lint and lang == "zh":
        errors.extend(check_term_confusion_zh(text))

    if args.evidence_dir is not None:
        # Only enforce attachment filename mentions when downloads exist
        names = []
        if args.evidence_dir.is_dir():
            names = _attachment_filenames_from_dir(args.evidence_dir)
        if names:
            errors.extend(check_attachment_mentions(text, args.evidence_dir, table))
        elif not args.quiet and args.evidence_dir.is_dir():
            print(
                "Note: --evidence-dir 无已下载附件文件名，跳过附件点名检查。",
                file=sys.stderr,
            )

    if by_id and not args.no_r001r002_hint:
        warnings.extend(check_r001_r002_crossref(text, by_id, loc, table))

    agg = aggregate_counts(by_id) if by_id else {}
    n_must = agg.get(loc.must, 0)
    n_should = agg.get(loc.should, 0)
    n_opt = agg.get(loc.optional, 0)
    n_total = len(by_id)

    declared = parse_declared_counts(text, loc)
    if declared is None:
        errors.append(
            "缺少可对账计数行（期望「计数：必须修复 N · 应当澄清 N · 可选 N」或 / 分隔）"
        )
    elif by_id:
        d0, d1, d2 = declared
        if (d0, d1, d2) != (n_must, n_should, n_opt):
            errors.append(
                _msg(
                    table,
                    "err_counts_mismatch",
                    d0=d0,
                    d1=d1,
                    d2=d2,
                    n0=n_must,
                    n1=n_should,
                    n2=n_opt,
                )
            )

    top_ids = extract_top_must_ids(text, loc)
    if top_ids is not None and by_id:
        must_set = {r for r, s in by_id.items() if s == loc.must}
        for rid in top_ids:
            if by_id.get(rid) != loc.must:
                errors.append(
                    _msg(
                        table,
                        "err_top_wrong_sev",
                        rid=rid,
                        sev=by_id.get(rid, "?" if lang == "en" else "未定义"),
                    )
                )
        if n_must <= 5 and must_set:
            top_set = set(top_ids)
            missing = sorted(must_set - top_set, key=rnum)
            if missing:
                errors.append(
                    _msg(
                        table,
                        "err_top_missing",
                        n=n_must,
                        missing=", ".join(missing),
                    )
                )
    elif not args.quiet and not args.brief:
        print(_msg(table, "note_no_top"), file=sys.stderr)

    if args.strict and warnings:
        errors.extend(warnings)
        warnings = []

    if not args.quiet:
        mode = "brief" if args.brief else "full"
        print(_msg(table, "summary_header", ver=__version__) + f" · mode={mode}")
        if by_id:
            print(
                _msg(
                    table,
                    "from_headings",
                    must=n_must,
                    should=n_should,
                    opt=n_opt,
                    n=n_total,
                )
            )
        if declared:
            dct = str(table.get("declared", ""))
            print(dct.format(declared[0], declared[1], declared[2]))
        if top_ids:
            print(_msg(table, "top_ids", ids=", ".join(top_ids)))

    for w in warnings:
        pfx = str(table.get("warning_prefix", "Warning: {0}"))
        print(pfx.format(w), file=sys.stderr)
    for e in errors:
        print(f"ERROR: {e}" if not e.startswith("ERROR") else e, file=sys.stderr)

    if errors:
        if not args.quiet:
            print(f"FAIL ({len(errors)} error(s))", file=sys.stderr)
        return 1
    if not args.quiet:
        print("PASS")
    return 0


def check_presentation_basics(
    text: str, *, brief: bool, table: dict[str, str]
) -> list[str]:
    """Structural checks aligned with skill presentation contract (not severity judgment)."""
    del table  # reserved for i18n
    errors: list[str] = []
    if not _SCOPE_RE.search(text):
        errors.append("缺少「范围」行（呈现契约 P1）")
    if brief and not _EVIDENCE_COVERAGE_RE.search(text):
        errors.append("brief 模式缺少 EVIDENCE_COVERAGE / 证据覆盖 小节")
    if re.search(r"跟票", text):
        errors.append("正文含「跟票」；请改为「另开 Story / 单独 Jira」（P10）")
    if re.search(r"本票范围", text):
        errors.append("勿用「本票范围」；直接写做什么（P1/P10）")
    return errors


def _get_locale(code: str) -> LocaleSpec:
    c = (code or "zh").strip().lower()[:2]
    if c == "en":
        return _EnLocale()
    if c not in ("zh", ""):
        raise ValueError(f"Unsupported --lang: {code!r} (use zh or en)")
    return _ZhLocale()


# User-visible strings: edit here for translations / wording changes.
# Keys are stable; values use str.format for placeholders.
def _S(lang: str) -> dict[str, str]:
    """Single place for all CLI output, errors, and notes. lang is 'zh' or 'en'."""
    if lang == "en":
        return {
            "ap_description": "Validate requirement_risk Markdown: severities, counts, Top, optional checks.",
            "help_evidence_dir": "Jira output dir (fetch_manifest.json); every downloaded attachment filename must appear in the report.",
            "help_strict": "Also fail on R-001/R-002 crossref warnings.",
            "help_no_term_lint": "Disable Chinese homophone term-lint (default off for en).",
            "help_no_r001r2": "Do not require R-001 in R-002 when both are MUST.",
            "help_lang": "Report language: zh (default) or en (MUST FIX / SHOULD CLARIFY / OPTIONAL headings).",
            "help_quiet": "Only print errors to stderr; suppress summary on stdout.",
            "empty_input": "Empty input.",
            "no_headings": "No #### R-00N · (required severity) · headings found (check --lang matches the report).",
            "summary_header": "validate_requirement_risk_report.py v{ver}",
            "from_headings": "  From headings: MUST={must} SHOULD={should} OPTIONAL={opt} R rows={n}",
            "declared": "  Declared counts:  {0} / {1} / {2}",
            "top_ids": "  Top R-ids: {ids}",
            "note_no_counts": "Note: no 'Counts: MUST X / SHOULD Y / OPTIONAL Z' line; skipping count line check.",
            "note_no_top": "Note: no 'MUST-FIX Top' block; skipping Top check.",
            "warning_prefix": "Warning: {0}",
            "err_duplicate": "Parse error: duplicate R-id {rid} with different severity",
            "err_counts_mismatch": (
                "Count line does not match FULL_UNKNOWN_MAP headings: "
                "declared MUST {d0} / SHOULD {d1} / OPTIONAL {d2}; "
                "from headings: MUST {n0} / SHOULD {n1} / OPTIONAL {n2}"
            ),
            "err_top_wrong_sev": (
                "MUST-FIX Top includes {rid}, but that row in FULL_UNKNOWN_MAP is «{sev}»"
            ),
            "err_top_missing": (
                "There are {n} MUST items (<=5); Top should list all; missing: {missing}"
            ),
            "err_evidence_dir_not_dir": "'--evidence-dir' is not a directory: {p}",
            "err_evidence_no_files": "No attachment filenames in fetch_manifest and no image files in {p}",
            "err_attachment_mention": (
                "Evidence: downloaded attachment not mentioned by filename in report: {name}"
            ),
            "warn_r001r2": (
                "Both R-001 and R-002 are MUST FIX, but the R-002 block does not mention R-001; "
                "link to R-001’s triage/acceptance in R-002 (Evidence/Notes)."
            ),
        }
    # zh
    return {
        "ap_description": "校验 requirement_risk 类 Markdown：严重级别、计数、Top 与可选项。",
        "help_evidence_dir": "Jira 拉取目录（含 fetch_manifest.json）；要求每个已下载附件文件名在报告中出现一次。",
        "help_strict": "将 R-001↔R-002 挂勾等建议也视为失败。",
        "help_no_term_lint": "关闭「监听器/听众」等常见笔误检查。",
        "help_no_r001r2": "不检查 R-001/R-002 均为必须修复时块内挂勾。",
        "help_lang": "报告语言：zh（默认，必须修复/应当澄清/可选）或 en（MUST FIX / …）。",
        "help_quiet": "仅将错误打 stderr，不输出摘要到 stdout。",
        "empty_input": "空输入。",
        "no_headings": "未找到 #### R-00N · 必须修复|应当澄清|可选 · 标题（请确认 --lang 与报告语言一致）。",
        "summary_header": "validate_requirement_risk_report.py v{ver}",
        "from_headings": "  From headings: 必须修复={must} 应当澄清={should} 可选={opt} 合计 R={n}",
        "declared": "  Declared 计数:  {0} / {1} / {2}",
        "top_ids": "  Top R-ids: {ids}",
        "note_no_counts": "Note: 无「计数：必须修复 X / 应当澄清 Y / 可选 Z」行，跳过计数行对账。",
        "note_no_top": "Note: 无「必须修复 Top」/ MUST-FIX top 块，跳过 Top 检查。",
        "warning_prefix": "Warning: {0}",
        "err_duplicate": "Parse error: duplicate R-id {rid} with different severity",
        "err_counts_mismatch": (
            "计数行与 FULL_UNKNOWN_MAP 标题不一致: 文内写 必须修复 {d0} / 应当澄清 {d1} / 可选 {d2}, "
            "由标题推导为 必须修复 {n0} / 应当澄清 {n1} / 可选 {n2}"
        ),
        "err_top_wrong_sev": "必须修复 Top 含 {rid}，但该条在 FULL_UNKNOWN_MAP 中为「{sev}」",
        "err_top_missing": "必须修复共 {n} 条 (<=5)，Top 应列全；缺少: {missing}",
        "err_evidence_dir_not_dir": "--evidence-dir 不是目录: {p}",
        "err_evidence_no_files": "未在 {p} 发现 fetch_manifest 附件名或可识别的图片文件",
        "err_attachment_mention": "证据覆盖：本地下载的附件未在正文中出现文件名: {name}（请在 EVIDENCE_COVERAGE 或相关「证据：」中点名）",
        "warn_r001r2": (
            "R-001 与 R-002 均为必须修复，但 R-002 块未显式出现 R-001，建议在 R-002「证据」或「补充」中挂勾 R-001 的排障结论/验收判据。"
        ),
    }


# Backtick-wrapped or bold/plain R-id in Top / 须先拍板 bullets
TOP_RID_RE = re.compile(r"`(R-\d+)`|\*\*(R-\d+)\*\*|(?<![A-Za-z0-9-])(R-\d+)(?![A-Za-z0-9-])")

_SCOPE_RE = re.compile(
    r"^(?:\*\*)?范围(?:\*\*)?\s*[:：]|^-\s*范围\s*[:：]",
    re.MULTILINE,
)
_EVIDENCE_COVERAGE_RE = re.compile(
    r"(?m)^(?:###?\s*)?(?:`?EVIDENCE_COVERAGE`?|证据覆盖)\b"
)

# zh only: 听众 vs 监听器
TERM_CONFUSION_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"解析[、,]\s*听众"), "「解析、听众」在负载均衡/入站排障语境下疑为笔误，应为「监听器」。"),
    (re.compile(r"听众[、,]\s*出网"), "「听众、出网」疑为笔误，前一词应为「监听器」。"),
    (re.compile(r"与\s*听众[（(]"), "「与听众(…」在网关/入站语境下疑为笔误，应为「监听器」。"),
]
TRIPLE_MISHEAR_RE = re.compile(r"解析[、,]\s*听众[、,]\s*出网")

IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")


def _msg(
    table: dict[str, str], key: str, **kwargs: Any
) -> str:
    v = table.get(key) or f"<missing:{key}>"
    if isinstance(v, str) and kwargs:
        return v.format(**kwargs)
    if isinstance(v, str):
        return v
    return str(v)


def parse_heading_severities(
    text: str, loc: LocaleSpec, table: dict[str, str]
) -> dict[str, str]:
    m: dict[str, str] = {}
    for match in loc.heading_re.finditer(text):
        rid, sev = match.group(1), match.group(2)
        if rid in m and m[rid] != sev:
            raise ValueError(_msg(table, "err_duplicate", rid=rid))
        m[rid] = sev
    return m


def check_term_confusion_zh(text: str) -> list[str]:
    if TRIPLE_MISHEAR_RE.search(text):
        return ["入站/排障列表中「解析、听众、出网」疑为笔误，其中「听众」应为「监听器」。"]
    err: list[str] = []
    for pat, msg in TERM_CONFUSION_PATTERNS:
        if pat.search(text):
            err.append(msg)
    return err


def check_attachment_mentions(
    text: str, evidence_dir: Path, table: dict[str, str]
) -> list[str]:
    if not evidence_dir.is_dir():
        return [_msg(table, "err_evidence_dir_not_dir", p=evidence_dir)]
    names = _attachment_filenames_from_dir(evidence_dir)
    if not names:
        return [_msg(table, "err_evidence_no_files", p=evidence_dir)]
    err: list[str] = []
    for name in names:
        if name not in text:
            err.append(_msg(table, "err_attachment_mention", name=name))
    return err


def check_r001_r002_crossref(
    text: str, by_id: dict[str, str], loc: LocaleSpec, table: dict[str, str]
) -> list[str]:
    if by_id.get("R-001") != loc.must or by_id.get("R-002") != loc.must:
        return []
    block = extract_heading_block(text, "R-002")
    if not block:
        return []
    if "R-001" in block:
        return []
    return [_msg(table, "warn_r001r2")]


def aggregate_counts(by_id: dict[str, str]) -> dict[str, int]:
    out: defaultdict[str, int] = defaultdict(int)
    for sev in by_id.values():
        out[sev] += 1
    return dict(out)


def parse_declared_counts(text: str, loc: LocaleSpec) -> tuple[int, int, int] | None:
    m = loc.counts_re.search(text)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def extract_top_must_ids(text: str, loc: LocaleSpec) -> list[str] | None:
    start = -1
    for sub in loc.top_starts:
        p = text.find(sub)
        if p >= 0 and (start < 0 or p < start):
            start = p
    if start < 0:
        return None
    tail = text[start:]
    end = len(tail)
    for em in loc.top_block_end_markers:
        p = tail.find(em)
        if p >= 0:
            end = min(end, p)
    block = tail[:end]
    ids: list[str] = []
    seen: set[str] = set()
    for line in block.splitlines():
        for m2 in TOP_RID_RE.finditer(line):
            rid = next((g for g in m2.groups() if g), None)
            if rid and rid not in seen:
                seen.add(rid)
                ids.append(rid)
    return ids if ids else None


def extract_heading_block(text: str, rid: str) -> str | None:
    m = re.search(rf"^####\s+{re.escape(rid)}\s+·", text, re.MULTILINE)
    if not m:
        return None
    rest = text[m.end() :]
    m2 = re.search(r"^####\s+R-\d+\s+·", rest, re.MULTILINE)
    if m2:
        return text[m.start() : m.end() + m2.start()]
    return text[m.start() :]


def rnum(rid: str) -> int:
    return int(rid.split("-", 1)[1])


def _attachment_filenames_from_dir(evidence_dir: Path) -> list[str]:
    manifest = evidence_dir / "fetch_manifest.json"
    if manifest.is_file():
        with open(manifest, encoding="utf-8") as f:
            data = json.load(f)
        at = data.get("attachments") or {}
        out: list[str] = []
        for d in at.get("downloaded") or []:
            fn = d.get("filename") or d.get("path")
            if fn:
                out.append(str(fn).strip())
        if out:
            return sorted(set(out), key=str.lower)
    return sorted(
        {p.name for p in evidence_dir.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES}
    )




if __name__ == "__main__":
    sys.exit(main())
