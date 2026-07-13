#!/usr/bin/env python3
"""Build conflict-ledger artifacts from S3/S4 artifacts."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_SCRIPTS = next(p for p in Path(__file__).resolve().parents if (p / "_install.py").is_file())
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
import _install

_install.bootstrap(__file__)

from runtime.domain_knowledge_paths import CURATED_BY_ROOT, confirmed_slugs_from_checklist, resolve_checklist_file
SECTION_RE = re.compile(r"^##\s+(.+)$")
BULLET_RE = re.compile(r"^-\s+(.+)$")


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build conflict ledger from S3/S4 artifacts.")
    p.add_argument("--root-id", required=True, help="Confluence root page ID")
    return p.parse_args()


def _confirmed_slugs(text: str) -> list[str]:
    return confirmed_slugs_from_checklist(text)


def _norm(text: str) -> str:
    lowered = str(text or "").lower()
    lowered = re.sub(r"[`'\"“”‘’]", " ", lowered)
    lowered = re.sub(r"[^0-9a-z\u4e00-\u9fff%._\-]+", " ", lowered)
    return " ".join(lowered.split())


def _extract_numbers(text: str) -> list[str]:
    vals = re.findall(r"\d+(?:\.\d+)?\s*(?:%|天|周|月|年|CVP|SVP|CNY|¥)?", str(text or ""), re.IGNORECASE)
    out: list[str] = []
    seen: set[str] = set()
    for v in vals:
        key = _norm(v)
        if key and key not in seen:
            seen.add(key)
            out.append(v.strip())
    return out[:6]


def _collect_s4_resolved(work_path: Path) -> list[str]:
    if not work_path.is_file():
        return []
    text = work_path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    in_section = False
    out: list[str] = []
    for ln in lines:
        m = SECTION_RE.match(ln.strip())
        if m:
            in_section = m.group(1).strip() == "口径裁决（跨页冲突处理）"
            continue
        if not in_section:
            continue
        bm = BULLET_RE.match(ln.strip())
        if bm:
            out.append(bm.group(1).strip())
    return out


def _build_pending_conflicts(props_path: Path) -> list[dict[str, object]]:
    if not props_path.is_file():
        return []
    payload = json.loads(props_path.read_text(encoding="utf-8"))
    groups: dict[str, dict[str, object]] = {}
    for page in list(payload.get("pages") or []):
        url = str(page.get("source_url") or "")
        for item in list(page.get("proposition_items") or []):
            text = str(item.get("text") or "").strip()
            if not text:
                continue
            block = dict(item.get("decision_block") or {})
            actor = str(block.get("actor") or "").strip()
            condition = str(block.get("condition") or "").strip()
            action = str(block.get("action") or "").strip()
            outcome = str(block.get("observable_outcome") or "").strip()
            window = str(block.get("time_window") or "").strip()
            question = str(item.get("decision_question") or "")
            if not question:
                question = "核心判定"
            topic_key = "|".join(
                x for x in [_norm(actor), _norm(action)[:48], _norm(outcome)[:48]] if x
            ) or _norm(text)[:96]
            g = groups.setdefault(
                f"{question}:{topic_key}",
                {
                    "question": question,
                    "actors": set(),
                    "conditions": set(),
                    "outcomes": set(),
                    "windows": set(),
                    "numbers": set(),
                    "evidence": set(),
                },
            )
            if actor:
                g["actors"].add(actor)
            if condition:
                g["conditions"].add(condition)
            if outcome:
                g["outcomes"].add(outcome)
            if window:
                g["windows"].add(window)
            for num in _extract_numbers(" ".join([text, condition, action, outcome, window])):
                g["numbers"].add(num)
            if url.startswith("http"):
                g["evidence"].add(url)

    pending: list[dict[str, object]] = []
    for g in groups.values():
        windows = sorted(x for x in g["windows"] if x)  # type: ignore[index]
        numbers = sorted(x for x in g["numbers"] if x)  # type: ignore[index]
        outcomes = sorted(x for x in g["outcomes"] if x)  # type: ignore[index]
        question = str(g["question"])
        evidence = sorted(x for x in g["evidence"] if x)[:3]  # type: ignore[index]
        if len(windows) >= 2:
            pending.append(
                {
                    "type": "时间窗冲突",
                    "question": question,
                    "detail": " / ".join(windows[:3]),
                    "evidence": evidence,
                }
            )
        if len(numbers) >= 2:
            pending.append(
                {
                    "type": "阈值口径冲突",
                    "question": question,
                    "detail": " / ".join(numbers[:4]),
                    "evidence": evidence,
                }
            )
        if len(outcomes) >= 2:
            pending.append(
                {
                    "type": "后果口径冲突",
                    "question": question,
                    "detail": " / ".join(outcomes[:3]),
                    "evidence": evidence,
                }
            )
    return pending


def _write_ledger(path: Path, slug: str, resolved: list[str], pending: list[dict[str, object]]) -> None:
    lines = [
        f"# {slug} · Conflict Ledger",
        "",
        "## 说明",
        "- 本台账由 S3/S4 产物生成，用于显式记录冲突候选与裁决状态。",
        "- 若无冲突，需明确记录“无显式冲突”。",
        "",
        "## 已裁决冲突",
    ]
    if not resolved:
        lines.append("- 无显式冲突。")
    else:
        for idx, item in enumerate(resolved, start=1):
            lines.append(f"- CL-{idx:03d} 冲突项：{item}")
            lines.append("  - 采用口径：见 S4 工作稿裁决条目")
            lines.append("  - 采用理由：由 Agent 在 S4 语义重挂载中给出")
            lines.append("  - 证据：见同条规则链证据页")
    lines.extend(["", "## 待确认冲突"])
    if not pending:
        lines.append("- 无待确认冲突。")
    else:
        base = len(resolved)
        for idx, item in enumerate(pending, start=1):
            lines.append(
                f"- CL-{base + idx:03d} 冲突项：{item.get('type')}（{item.get('question')}）：{item.get('detail')}"
            )
            lines.append("  - 待确认人：待定")
            lines.append("  - 截止时间窗：待定")
            refs = list(item.get("evidence") or [])
            lines.append(f"  - 证据：{', '.join(refs) if refs else '待补录证据'}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    args = _parse_args()
    root_id = str(args.root_id).strip()
    curated_root = CURATED_BY_ROOT / root_id
    checklist = resolve_checklist_file(curated_root)
    if checklist is None:
        print(f"Missing checklist: {curated_root / 'DOMAIN_MODULE_CHECKLIST.md'}", file=sys.stderr)
        return 1

    built = 0
    for slug in _confirmed_slugs(checklist.read_text(encoding="utf-8", errors="replace")):
        agg = curated_root / "_aggregate" / slug
        props = agg / f"{slug}-propositions.json"
        work_candidates = sorted((curated_root / "_deliver" / slug).glob("*领域知识-工作稿.md"))
        resolved = _collect_s4_resolved(work_candidates[0]) if work_candidates else []
        pending = _build_pending_conflicts(props)
        _write_ledger(agg / f"{slug}-conflict-ledger.md", slug, resolved, pending)
        built += 1
    print(f"Conflict ledger sync: built={built}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
