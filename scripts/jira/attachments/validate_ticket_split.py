#!/usr/bin/env python3
"""
Validate a ticket-splitter Markdown draft for structure + pseudo-testable bans.

First principles (what this script is for):
- Catch *explicit* delivery defects that make a split unusable in planning:
  missing 范围 / 拆单一览, missing per-item fields, done_when that is not observable.
- Do *not* decide how many items to split into, or whether the split axis is correct.
  Those are Agent / ticket_system concerns.

Exit 0 if OK, 1 if errors.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

__version__ = "1.2.0"

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

_SCOPE_RE = re.compile(
    r"^(?:\*\*)?范围(?:\*\*)?\s*[:：]|^-\s*范围\s*[:：]",
    re.MULTILINE,
)
_OVERVIEW_RE = re.compile(r"(?m)^##\s*拆单一览\s*$")

# Item section headers (presentation contract + ticket_system English labels)
_ITEM_HEADER_RE = re.compile(
    r"(?m)^(?:"
    r"Spike\s+\d+"
    r"|用户故事\s*\d+(?:\s*[（(]User Story[）)])?"
    r"|技术任务\s*\d+"
    r"|User Story\s+\d+"
    r"|Tech Task\s+\d+"
    r")\s*[:：]?\s*$"
)

# Field labels: Chinese presentation and/or English rule keys
_FIELD_PATTERNS: dict[str, re.Pattern[str]] = {
    "title": re.compile(
        r"(?m)^(?:-\s*)?(?:\*\*)?(?:标题|title)(?:\*\*)?(?:\s*[（(]title[）)])?\s*[:：]"
    ),
    "scope": re.compile(
        r"(?m)^(?:-\s*)?(?:\*\*)?(?:范围|scope)(?:\*\*)?(?:\s*[（(]scope[）)])?\s*[:：]"
    ),
    "done_when": re.compile(
        r"(?m)^(?:-\s*)?(?:\*\*)?(?:验收标准|done_when)(?:\*\*)?"
        r"(?:\s*[（(]done_when[）)])?\s*[:：]"
    ),
    "depends_on": re.compile(
        r"(?m)^(?:-\s*)?(?:\*\*)?(?:依赖|depends_on)(?:\*\*)?"
        r"(?:\s*[（(]depends_on[）)])?\s*[:：]"
    ),
    "confidence": re.compile(
        r"(?m)^(?:-\s*)?(?:\*\*)?(?:信心|confidence)(?:\*\*)?"
        r"(?:\s*[（(]confidence[）)])?\s*[:：]"
    ),
}

# Pseudo-testable / handoff language that is not an observable completion surface
_PSEUDO_DONE_RE = re.compile(
    r"(开发完成|开发完毕|代码完成|提测|送测|ready\s+for\s+(?:qa|test)|"
    r"handoff\s+to\s+qa|可以提测|开发已完成)",
    re.IGNORECASE,
)

# Weak positive signals that something observable was stated (heuristic, not semantic judge)
_OBSERVABLE_HINT_RE = re.compile(
    r"(可见|展示|返回|状态|接口|契约|构建|CI|通过|失败|页面|提示|"
    r"可观察|用户|顾问|响应|字段|事件|迁移|兼容|冒烟|断言|日志|"
    r"observable|user-visible|contract|build|passes?|fails?)",
    re.IGNORECASE,
)

_CONFIDENCE_VALUE_RE = re.compile(
    r"(?mi)(?:信心|confidence)[^\n]{0,40}?([01](?:\.\d+)?|\.\d+)"
)

_DEP_LABEL_RE = re.compile(r"\((?:blocking|validation|soft)\)|无")


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Validate ticket-splitter draft (structure + pseudo-testable bans)."
    )
    p.add_argument("path", nargs="?", help="Markdown file (default: stdin)")
    p.add_argument(
        "--brief",
        action="store_true",
        help="Brief mode: only require 范围 + ## 拆单一览; skip per-item fields.",
    )
    p.add_argument("-q", "--quiet", action="store_true", help="Less stdout on success.")
    p.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors.",
    )
    return p.parse_args()


def _read_text(path: str | None) -> str:
    if path:
        return Path(path).read_text(encoding="utf-8")
    return sys.stdin.read()


def _split_item_blocks(text: str) -> list[tuple[str, str]]:
    """Return [(header, body), ...] for decomposition items."""
    matches = list(_ITEM_HEADER_RE.finditer(text))
    if not matches:
        return []
    blocks: list[tuple[str, str]] = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        blocks.append((m.group(0).strip(), text[start:end]))
    return blocks


def _done_when_sections(body: str) -> list[str]:
    """Extract text under done_when / 验收标准 until next known field or end."""
    parts: list[str] = []
    for m in _FIELD_PATTERNS["done_when"].finditer(body):
        rest = body[m.end() :]
        # Stop at next field label
        stop = len(rest)
        for key, pat in _FIELD_PATTERNS.items():
            if key == "done_when":
                continue
            nm = pat.search(rest)
            if nm and nm.start() < stop:
                stop = nm.start()
        parts.append(rest[:stop].strip())
    return parts


def check_structure(text: str, *, brief: bool) -> list[str]:
    errors: list[str] = []
    if not _SCOPE_RE.search(text):
        errors.append("缺少「范围」行（P1）")
    if not _OVERVIEW_RE.search(text):
        errors.append("缺少「## 拆单一览」小节（P5）")
    if brief:
        return errors

    blocks = _split_item_blocks(text)
    if not blocks:
        errors.append(
            "完整模式未找到分解项标题（期望 Spike N / 用户故事 N / 技术任务 N 等）"
        )
        return errors

    for header, body in blocks:
        missing = [
            name
            for name, pat in _FIELD_PATTERNS.items()
            if not pat.search(body) and not pat.search(header + "\n" + body)
        ]
        # title may appear as first line after header without label in some drafts;
        # still require explicit label per presentation contract.
        if missing:
            errors.append(f"「{header}」缺少字段: {', '.join(missing)}")
    return errors


def check_pseudo_testable(text: str, *, brief: bool) -> list[str]:
    errors: list[str] = []
    if brief:
        # In brief mode, scan 拆单一览 + 纠偏 for pseudo language without observable hint
        overview_m = _OVERVIEW_RE.search(text)
        if not overview_m:
            return errors
        chunk = text[overview_m.start() :]
        # Stop before first item header if any leaked in
        item_m = _ITEM_HEADER_RE.search(chunk)
        if item_m:
            chunk = chunk[: item_m.start()]
        for m in _PSEUDO_DONE_RE.finditer(chunk):
            window = chunk[max(0, m.start() - 40) : m.end() + 80]
            if not _OBSERVABLE_HINT_RE.search(window):
                errors.append(
                    f"brief 一览/纠偏含伪可测措辞「{m.group(0)}」且附近无可观测提示"
                )
        return errors

    for header, body in _split_item_blocks(text):
        sections = _done_when_sections(body)
        if not sections:
            continue
        for sec in sections:
            for m in _PSEUDO_DONE_RE.finditer(sec):
                # P2: ban phrase is never a valid completion surface
                errors.append(
                    f"「{header}」验收标准禁止以「{m.group(0)}」作为完成面；"
                    "请改写为可观测结果（用户可见行为 / 系统状态 / 契约）"
                )
    return errors


def check_confidence_and_deps(text: str, *, brief: bool) -> list[str]:
    if brief:
        return []
    warnings: list[str] = []
    for header, body in _split_item_blocks(text):
        if _FIELD_PATTERNS["confidence"].search(body):
            vals = _CONFIDENCE_VALUE_RE.findall(body)
            if not vals:
                warnings.append(f"「{header}」有信心字段但未解析到 0–1 数值")
            else:
                try:
                    v = float(vals[0])
                    if not 0.0 <= v <= 1.0:
                        warnings.append(f"「{header}」confidence={v} 超出 [0,1]")
                except ValueError:
                    warnings.append(f"「{header}」confidence 无法解析")
        if _FIELD_PATTERNS["depends_on"].search(body):
            # Extract depends_on block roughly
            dm = _FIELD_PATTERNS["depends_on"].search(body)
            assert dm is not None
            rest = body[dm.end() :]
            stop = len(rest)
            for key, pat in _FIELD_PATTERNS.items():
                if key == "depends_on":
                    continue
                nm = pat.search(rest)
                if nm and nm.start() < stop:
                    stop = nm.start()
            dep_block = rest[:stop]
            if dep_block.strip() and not _DEP_LABEL_RE.search(dep_block):
                warnings.append(
                    f"「{header}」依赖块未出现「无」或 (blocking|validation|soft) 标签"
                )
    return warnings


def check_term_noise_zh(text: str) -> list[str]:
    """Ban internal jargon that presentation contract forbids."""
    errors: list[str] = []
    if re.search(r"跟票", text):
        errors.append("正文含「跟票」；请改为「另开 Story / 单独 Jira」（P10）")
    # 「本票」 as scope label is noisy; allow rare technical quotes
    if re.search(r"本票范围", text):
        errors.append("勿用「本票范围」；直接写做什么（P1/P10）")
    # English out-of-scope calques: process nouns instead of observable result boundaries
    if re.search(r"完整取消[^。\n]{0,12}(链路|闭环|流程)", text):
        errors.append(
            "勿用「完整取消…链路/闭环/流程」；改为可观察结果边界"
            "（如不含确认后报名变为已取消及后续处理）（P10）"
        )
    if re.search(r"取消落库", text):
        errors.append(
            "勿用「取消落库」作范围黑话；写清不做哪种可见状态（P10）"
        )
    return errors


_TITLE_VALUE_RE = re.compile(
    r"(?m)^(?:-\s*)?(?:\*\*)?(?:标题|title)(?:\*\*)?(?:\s*[（(]title[）)])?\s*[:：]\s*(.+)$"
)
# Explicit P11 anti-patterns (signal only; not a semantic judge of “good prose”)
_TITLE_STACK_RE = re.compile(r"、.+[与和]")
_TITLE_CRYPTIC_RE = re.compile(r"直下")
_TITLE_EMPTY_OPEN_RE = re.compile(r"^开放(?:\s|$)")


def check_title_headline(text: str, *, brief: bool) -> list[str]:
    """P11: title is a one-primary-outcome headline, not a scope bullet dump."""
    if brief:
        return []
    errors: list[str] = []
    for header, body in _split_item_blocks(text):
        for m in _TITLE_VALUE_RE.finditer(body):
            title = m.group(1).strip()
            if _TITLE_STACK_RE.search(title):
                errors.append(
                    f"「{header}」标题疑似顿号/`与`堆多条改动（P11）：「{title}」；"
                    "只保留一个主结果，其余进 scope"
                )
            if _TITLE_CRYPTIC_RE.search(title):
                errors.append(
                    f"「{header}」标题含私货缩写「直下」（P11）；请写完整「直接下载」等"
                )
            if _TITLE_EMPTY_OPEN_RE.search(title):
                errors.append(
                    f"「{header}」标题以空动词「开放」起句（P11）；请改为对象+可观察结果"
                )
    return errors


def _scope_bullet_lines(body: str) -> list[str]:
    """Extract bullet lines under scope / 范围 until next known field."""
    sm = _FIELD_PATTERNS["scope"].search(body)
    if not sm:
        return []
    rest = body[sm.end() :]
    stop = len(rest)
    for key, pat in _FIELD_PATTERNS.items():
        if key == "scope":
            continue
        nm = pat.search(rest)
        if nm and nm.start() < stop:
            stop = nm.start()
    block = rest[:stop]
    return [
        ln.strip()
        for ln in block.splitlines()
        if re.match(r"^-\s+\S", ln.strip())
    ]


# P12: welded「覆盖 X：A；B / C」inventory line
_SCOPE_WELD_RE = re.compile(r"覆盖.+[：:].+[；;].+/")


def check_scope_one_concern(text: str, *, brief: bool) -> list[str]:
    """P12: each scope bullet is one orally scannable concern."""
    if brief:
        return []
    errors: list[str] = []
    for header, body in _split_item_blocks(text):
        for line in _scope_bullet_lines(body):
            # strip leading "- "
            content = re.sub(r"^-\s+", "", line)
            if _SCOPE_WELD_RE.search(content):
                errors.append(
                    f"「{header}」scope 疑似把多关注点焊成一句（P12）：「{content}」；"
                    "拆成多条 bullet（一条一意）"
                )
            elif content.count("；") >= 2 and "/" in content:
                errors.append(
                    f"「{header}」scope 分号过多且含「/」枚举（P12）：「{content}」；"
                    "拆成多条或改成整句口语"
                )
    return errors


def main() -> int:
    args = _parse_args()
    try:
        text = _read_text(args.path)
    except OSError as e:
        print(f"无法读取输入: {e}", file=sys.stderr)
        return 1

    if not text.strip():
        print("输入为空", file=sys.stderr)
        return 1

    errors: list[str] = []
    warnings: list[str] = []

    errors.extend(check_structure(text, brief=args.brief))
    errors.extend(check_pseudo_testable(text, brief=args.brief))
    errors.extend(check_term_noise_zh(text))
    errors.extend(check_title_headline(text, brief=args.brief))
    errors.extend(check_scope_one_concern(text, brief=args.brief))
    warnings.extend(check_confidence_and_deps(text, brief=args.brief))

    if args.strict and warnings:
        errors.extend(warnings)
        warnings = []

    if not args.quiet:
        mode = "brief" if args.brief else "full"
        print(f"validate_ticket_split {__version__} · mode={mode}", flush=True)
        if args.path:
            print(f"file: {args.path}", flush=True)

    for w in warnings:
        print(f"WARN: {w}", file=sys.stderr)
    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)

    if errors:
        if not args.quiet:
            print(f"FAIL ({len(errors)} error(s))", file=sys.stderr)
        return 1

    if not args.quiet:
        print("PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
