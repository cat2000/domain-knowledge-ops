#!/usr/bin/env python3
"""Build decision-atom artifacts from S3 aggregate artifacts."""
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

AXIS_RE = {
    "可见性判定": re.compile(r"(可见|展示|显示|隐藏|入口|卡片|文案)", re.IGNORECASE),
    "资格判定": re.compile(r"(资格|达标|晋升|报名|审核|通过|不通过|eligible|qualified)", re.IGNORECASE),
    "结算判定": re.compile(r"(奖金|奖励|分红|结算|发放|cvp|svp|fpv|金额)", re.IGNORECASE),
    "流程判定": re.compile(r"(提交|支付|下单|流程|可继续|中断|创建|取消)", re.IGNORECASE),
    "状态迁移判定": re.compile(r"(状态|in_progress|qualified|finalized|迁移|终态|倒计时)", re.IGNORECASE),
}


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build decision-atom artifacts from S3 artifacts.")
    p.add_argument("--root-id", required=True, help="Confluence root page ID")
    return p.parse_args()


def _confirmed_slugs(text: str) -> list[str]:
    return confirmed_slugs_from_checklist(text)


def _classify_decision_question(text: str, fallback: str = "UNKNOWN") -> str:
    scores: list[tuple[int, str]] = []
    for axis, patt in AXIS_RE.items():
        scores.append((len(patt.findall(text)), axis))
    scores.sort(key=lambda x: x[0], reverse=True)
    if not scores or scores[0][0] == 0:
        return fallback
    return scores[0][1]


def _canonical_branch_ids(values: list[object]) -> list[str]:
    out: list[str] = []
    for raw in values:
        token = str(raw or "").strip().lower().replace(" ", "")
        if token in {"branch_1", "branch1", "phase1", "challenge1", "challengeone", "1stchallenge", "第一阶段", "挑战一"}:
            val = "branch_1"
        elif token in {"branch_2", "branch2", "phase2", "challenge2", "challengetwo", "2ndchallenge", "第二阶段", "挑战二"}:
            val = "branch_2"
        else:
            continue
        if val not in out:
            out.append(val)
    return out


def _atom_from_item(
    slug: str,
    idx: int,
    page: dict[str, object],
    item: dict[str, object],
) -> dict[str, object]:
    text = str(item.get("text") or "").strip()
    block = dict(item.get("decision_block") or {})
    branch_ids = _canonical_branch_ids(list(item.get("branch_tags") or item.get("branch_ids") or []))
    actor = str(block.get("actor") or "").strip()
    condition = str(block.get("condition") or "").strip()
    action = str(block.get("action") or "").strip()
    outcome = str(block.get("observable_outcome") or "").strip()
    time_window = str(block.get("time_window") or "").strip()
    exception = str(block.get("exception") or "").strip()
    source_url = str(page.get("source_url") or "").strip()
    materialized_file = str(page.get("materialized_file") or "").strip()
    evidence_refs = [source_url] if source_url.startswith("http") else []
    if materialized_file:
        evidence_refs.append(materialized_file)
    placeholder = bool(re.search(r"(no-text|待补录|无正文)", text, re.IGNORECASE))
    decision_question = str(item.get("decision_question") or "").strip()
    if decision_question in {"", "UNKNOWN", "MIXED"}:
        decision_question = _classify_decision_question(" ".join([text, condition, action, outcome]), fallback="流程判定")
    missing_fields = [
        key
        for key, value in {
            "actor": actor,
            "condition": condition,
            "branch_action": action,
            "observable_outcome": outcome,
            "time_window": time_window,
            "exception": exception,
        }.items()
        if not value
    ]
    return {
        "atom_id": f"{slug}-A{idx:03d}",
        "source_rule_heading": text[:120] or f"{slug}-rule-{idx}",
        "semantic_roles": list(item.get("semantic_roles") or []),
        "semantic_preservation_reason": str(item.get("semantic_preservation_reason") or ""),
        "business_scope_label": str(item.get("business_scope_label") or item.get("semantic_scope_label") or ""),
        "decision_question": decision_question,
        "actor": actor,
        "condition": condition,
        "branch_action": action,
        "branch_ids": branch_ids,
        "branch_list": " | ".join(branch_ids),
        "branch_condition": condition if branch_ids else "",
        "branch_outcome": outcome if branch_ids else "",
        "observable_outcome": outcome,
        "time_window": time_window,
        "exception": exception,
        "evidence_refs": evidence_refs,
        "missing_fields": missing_fields,
        "is_placeholder": placeholder,
    }


def _build_atoms_for_slug(curated_root: Path, slug: str) -> list[dict[str, object]]:
    agg_dir = curated_root / "_aggregate" / slug
    props_path = agg_dir / f"{slug}-propositions.json"
    if not props_path.is_file():
        return []
    props_payload = json.loads(props_path.read_text(encoding="utf-8"))

    atoms: list[dict[str, object]] = []
    idx = 0
    for page in list(props_payload.get("pages") or []):
        for item in list(page.get("proposition_items") or []):
            if str(item.get("candidate_type") or "") != "contract_candidate":
                continue
            text = str(item.get("text") or "").strip()
            if not text:
                continue
            idx += 1
            atoms.append(_atom_from_item(slug, idx, page, item))
    return atoms


def _write_atom_artifacts(agg_dir: Path, slug: str, atoms: list[dict[str, object]]) -> None:
    agg_dir.mkdir(parents=True, exist_ok=True)
    json_path = agg_dir / f"{slug}-decision-atoms.json"
    md_path = agg_dir / f"{slug}-decision-atoms.md"
    payload = {"slug": slug, "atoms_total": len(atoms), "atoms": atoms}
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        f"# {slug} · Decision Atoms",
        "",
        "## 说明",
        "- 本文件由 S3 结构化产物生成，不依赖 S5 文本。",
        "- 原子层用于门禁与审阅，不替代 S4/S5 读者向叙事。",
        "",
        "## 原子清单",
    ]
    for atom in atoms:
        lines.append(f"### {atom['atom_id']} · {atom['decision_question']}")
        lines.append(f"- 来源候选：{atom['source_rule_heading']}")
        lines.append(f"- 业务作用域：{atom.get('business_scope_label') or 'global'}")
        roles = atom.get("semantic_roles") or []
        lines.append(f"- 语义角色：{', '.join(roles) if roles else '（缺）'}")
        lines.append(f"- 判定对象：{atom['actor']}")
        lines.append(f"- 条件：{atom['condition']}")
        lines.append(f"- 分支动作：{atom['branch_action']}")
        lines.append(f"- 可见后果：{atom['observable_outcome']}")
        lines.append(f"- 时间窗：{atom['time_window']}")
        lines.append(f"- 例外：{atom['exception']}")
        lines.append(f"- 分支ID：{', '.join(atom.get('branch_ids') or []) or '（无）'}")
        refs = atom.get("evidence_refs") or []
        lines.append(f"- 证据：{', '.join(refs) if refs else '（缺）'}")
        lines.append("")
    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    args = _parse_args()
    root_id = str(args.root_id).strip()
    curated_root = CURATED_BY_ROOT / root_id
    checklist = resolve_checklist_file(curated_root)
    if checklist is None:
        print(f"Missing checklist: {curated_root / 'DOMAIN_MODULE_CHECKLIST.md'}", file=sys.stderr)
        return 1

    slugs = _confirmed_slugs(checklist.read_text(encoding="utf-8", errors="replace"))
    built = 0
    for slug in slugs:
        agg_dir = curated_root / "_aggregate" / slug
        props_path = agg_dir / f"{slug}-propositions.json"
        if not props_path.is_file():
            continue
        atoms = _build_atoms_for_slug(curated_root, slug)
        _write_atom_artifacts(agg_dir, slug, atoms)
        built += 1
    print(f"Decision atom sync: built={built}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
