#!/usr/bin/env python3
"""Cross-module S3 quality gate (contract density + signal fidelity)."""
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

from runtime.domain_knowledge_paths import CURATED_BY_ROOT, is_checklist_status_confirmed, resolve_checklist_file

SLUG_RE = re.compile(r"（([^）]+)）")
_DELIVER_SLUG_RE = re.compile(r"_deliver/([a-z0-9-]+)/")
NUMERIC_ANCHOR_RE = re.compile(
    r"\d+(?:,\d{3})*(?:\.\d+)?\s*(?:%|天|周|月|年|CVP|SVP|FPV|CNY|¥)?",
    re.IGNORECASE,
)
BRANCH_1_RE = re.compile(r"(挑战一|第一阶段|branch\s*1|phase\s*1|challenge\s*one|1st\s*challenge)", re.IGNORECASE)
BRANCH_2_RE = re.compile(r"(挑战二|第二阶段|branch\s*2|phase\s*2|challenge\s*two|2nd\s*challenge)", re.IGNORECASE)
OUTCOME_RE = re.compile(r"(获得|发放|结算|展示|可见|通过|拒绝|进入|状态|eligible|qualified|receive)", re.IGNORECASE)
TIME_RE = re.compile(r"(\d+\s*(?:天|周|月|年)|每日|每周|每月|weekly|monthly|daily)", re.IGNORECASE)


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="S3 cross-module quality gate.")
    p.add_argument("--root-id", required=True, help="Confluence root page ID")
    p.add_argument("--warn-only", action="store_true")
    p.add_argument("--min-items-for-rate", type=int, default=30)
    p.add_argument("--min-signal-for-unknown", type=int, default=20)
    p.add_argument("--min-contract-coverage", type=float, default=0.07)
    p.add_argument("--min-high-confidence-rate", type=float, default=0.12)
    p.add_argument("--max-unknown-rate", type=float, default=0.85)
    p.add_argument("--min-branch-integrity", type=float, default=0.20)
    p.add_argument("--min-stage1-samples", type=int, default=12)
    p.add_argument("--min-distinct-stage1-sources", type=int, default=2)
    p.add_argument("--max-stage1-source-share", type=float, default=0.70)
    p.add_argument(
        "--report-json",
        default="S3_QUALITY_REPORT.json",
        help="Report filename written under curated/by-root/<root-id>/ (set empty to disable)",
    )
    p.add_argument(
        "--report-md",
        default="S3_QUALITY_REPORT.md",
        help="Markdown report filename written under curated/by-root/<root-id>/ (set empty to disable)",
    )
    return p.parse_args()


def _confirmed_slugs(text: str) -> list[str]:
    from runtime.domain_knowledge_paths import confirmed_slugs_from_checklist

    return confirmed_slugs_from_checklist(text)


def _non_empty_fields(item: dict[str, object]) -> int:
    n = int(item.get("decision_fields_count") or 0)
    if n > 0:
        return n
    block = dict(item.get("decision_block") or {})
    return sum(1 for v in block.values() if str(v).strip())


def _slug_metrics_map(report: dict[str, object]) -> dict[str, dict[str, object]]:
    out: dict[str, dict[str, object]] = {}
    for row in list(report.get("slug_metrics") or []):
        d = dict(row)
        slug = str(d.get("slug") or "").strip()
        if slug:
            out[slug] = d
    return out


def _compute_trend(prev_payload: dict[str, object] | None, curr_payload: dict[str, object]) -> dict[str, object]:
    if prev_payload is None:
        return {"status": "first_run"}

    prev_slugs = _slug_metrics_map(prev_payload)
    curr_slugs = _slug_metrics_map(curr_payload)
    common = sorted(set(prev_slugs) & set(curr_slugs))
    if not common:
        return {"status": "no_common_slugs"}

    metrics = [
        ("contract_coverage", True),
        ("high_confidence_rate", True),
        ("unknown_rate", False),
        ("branch_integrity", True),
    ]
    mean_delta: dict[str, float] = {}
    regressions: list[dict[str, object]] = []
    for key, higher_is_better in metrics:
        values: list[float] = []
        for slug in common:
            prev_v = float(prev_slugs[slug].get(key) or 0.0)
            curr_v = float(curr_slugs[slug].get(key) or 0.0)
            delta = curr_v - prev_v
            values.append(delta)
            if higher_is_better:
                degraded = delta < -0.01
            else:
                degraded = delta > 0.01
            if degraded:
                regressions.append({"slug": slug, "metric": key, "delta": round(delta, 6)})
        mean_delta[key] = round(sum(values) / len(values), 6)

    prev_issues = int(prev_payload.get("issues_total") or 0)
    curr_issues = int(curr_payload.get("issues_total") or 0)
    return {
        "status": "ok",
        "common_slugs": len(common),
        "mean_delta": mean_delta,
        "issues_delta": curr_issues - prev_issues,
        "regressions": regressions,
    }


def _write_reports(
    curated_root: Path,
    json_name: str,
    md_name: str,
    payload: dict[str, object],
) -> None:
    prev_payload = None
    if json_name:
        out_json = curated_root / json_name
        if out_json.is_file():
            try:
                prev_payload = dict(json.loads(out_json.read_text(encoding="utf-8")))
            except Exception:
                prev_payload = None
    payload["trend"] = _compute_trend(prev_payload, payload)

    if json_name:
        out_json = curated_root / json_name
        out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if md_name:
        out_md = curated_root / md_name
        lines = [
            f"# S3 质量报告 · root `{payload.get('root_id')}`",
            "",
            "## 阈值",
        ]
        thresholds = dict(payload.get("thresholds") or {})
        for k in sorted(thresholds.keys()):
            lines.append(f"- `{k}`: {thresholds[k]}")
        lines.extend(["", "## 模块指标", "| slug | items | signal_items | contract_coverage | high_conf_rate | missing_track_rate | branch_integrity | stage1_max_source_share | issues |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|"])
        for row in list(payload.get("slug_metrics") or []):
            d = dict(row)
            lines.append(
                f"| {d.get('slug')} | {d.get('items_total')} | {d.get('signal_items_total')} | "
                f"{float(d.get('contract_coverage') or 0):.3f} | {float(d.get('high_confidence_rate') or 0):.3f} | "
                f"{float(d.get('unknown_rate') or 0):.3f} | {float(d.get('branch_integrity') or 0):.3f} | "
                f"{float(d.get('stage1_max_source_share') or 0):.3f} | {len(list(d.get('issues') or []))} |"
            )
        trend = dict(payload.get("trend") or {})
        lines.extend(["", "## 趋势"])
        status = str(trend.get("status") or "")
        if status == "first_run":
            lines.append("- 首次生成报告，暂无历史对比。")
        elif status == "no_common_slugs":
            lines.append("- 无共同 slug，暂无可比趋势。")
        else:
            lines.append(f"- common_slugs: {trend.get('common_slugs')}")
            mean_delta = dict(trend.get("mean_delta") or {})
            for k in (
                "contract_coverage",
                "high_confidence_rate",
                "unknown_rate",
                "branch_integrity",
            ):
                v = float(mean_delta.get(k) or 0)
                sign = "+" if v >= 0 else ""
                lines.append(f"- Δ{k}: {sign}{v:.3f}")
            issues_delta = int(trend.get("issues_delta") or 0)
            issues_sign = "+" if issues_delta >= 0 else ""
            lines.append(f"- Δissues_total: {issues_sign}{issues_delta}")
            regressions = list(trend.get("regressions") or [])
            lines.append(f"- regressions: {len(regressions)}")
            for row in regressions[:8]:
                r = dict(row)
                delta = float(r.get("delta") or 0)
                sign = "+" if delta >= 0 else ""
                lines.append(f"  - {r.get('slug')} / {r.get('metric')}: {sign}{delta:.3f}")
        lines.extend(["", "## 结论", f"- checked_confirmed_slugs: {payload.get('checked_confirmed_slugs')}", f"- total_issues: {payload.get('issues_total')}"])
        out_md.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    args = _parse_args()
    root_id = str(args.root_id).strip()
    curated_root = CURATED_BY_ROOT / root_id
    checklist = resolve_checklist_file(curated_root)
    if checklist is None:
        print(f"Missing checklist: {curated_root / 'DOMAIN_MODULE_CHECKLIST.md'}", file=sys.stderr)
        return 0 if args.warn_only else 1

    issues: list[str] = []
    checked = 0
    slug_metrics: list[dict[str, object]] = []
    for slug in _confirmed_slugs(checklist.read_text(encoding="utf-8", errors="replace")):
        agg = curated_root / "_aggregate" / slug
        propositions_json = agg / f"{slug}-propositions.json"
        if not propositions_json.is_file():
            continue
        checked += 1

        props_payload = json.loads(propositions_json.read_text(encoding="utf-8"))
        items: list[dict[str, object]] = []
        for page in list(props_payload.get("pages") or []):
            items.extend(list(page.get("proposition_items") or []))
        if not items:
            issues.append(f"{slug}: empty proposition_items")
            slug_metrics.append(
                {
                    "slug": slug,
                    "items_total": 0,
                    "signal_items_total": 0,
                    "contract_coverage": 0.0,
                    "high_confidence_rate": 0.0,
                    "unknown_rate": 1.0,
                    "branch_integrity": 1.0,
                    "issues": ["empty proposition_items"],
                }
            )
            continue
        contract_items = [
            it
            for it in items
            if str(it.get("candidate_type") or "") in {"", "contract_candidate"}
        ]
        stage1_accepted_items = [
            it
            for it in items
            if str(it.get("admission_stage1_result") or "").strip() == "accepted"
        ]
        total = len(contract_items)
        slug_issues: list[str] = []

        contract_coverage = 1.0
        high_confidence_rate = 1.0
        if total > 0:
            contract_coverage = (
                sum(1 for it in contract_items if _non_empty_fields(it) >= 3) / total
            )
            high_confidence_rate = (
                sum(1 for it in contract_items if int(it.get("decision_confidence") or 0) >= 4) / total
            )

        if total >= args.min_items_for_rate and contract_coverage < args.min_contract_coverage:
            slug_issues.append(
                f"low contract coverage {contract_coverage:.3f} < {args.min_contract_coverage:.3f}"
            )
        if total >= args.min_items_for_rate and high_confidence_rate < args.min_high_confidence_rate:
            slug_issues.append(
                f"low high-confidence rate {high_confidence_rate:.3f} < {args.min_high_confidence_rate:.3f}"
            )

        signal_items = [
            it
            for it in contract_items
            if OUTCOME_RE.search(str(it.get("text") or ""))
            or TIME_RE.search(str(it.get("text") or ""))
            or bool(it.get("branch_ids"))
            or bool(NUMERIC_ANCHOR_RE.search(str(it.get("text") or "")))
        ]
        unknown_rate = 0.0
        if signal_items:
            unknown_rate = (
                sum(
                    1
                    for it in signal_items
                    if not str(it.get("decision_track") or "").strip()
                )
                / len(signal_items)
            )
            if len(signal_items) >= args.min_signal_for_unknown and unknown_rate > args.max_unknown_rate:
                slug_issues.append(
                    f"high missing decision_track rate {unknown_rate:.3f} > {args.max_unknown_rate:.3f}"
                )

        explicit_b1 = any(BRANCH_1_RE.search(str(it.get("text") or "")) for it in contract_items)
        explicit_b2 = any(BRANCH_2_RE.search(str(it.get("text") or "")) for it in contract_items)
        b1_count = sum(1 for it in contract_items if "branch_1" in set(it.get("branch_ids") or []))
        b2_count = sum(1 for it in contract_items if "branch_2" in set(it.get("branch_ids") or []))
        integrity = 1.0
        if explicit_b1 and explicit_b2 and (b1_count + b2_count) >= 8:
            integrity = min(b1_count, b2_count) / max(b1_count, b2_count)
            if integrity < args.min_branch_integrity:
                slug_issues.append(
                    f"low branch integrity {integrity:.3f} < {args.min_branch_integrity:.3f} (b1={b1_count}, b2={b2_count})"
                )

        stage1_max_source_share = 0.0
        stage1_dominant_source = ""
        stage1_total = len(stage1_accepted_items)
        if stage1_total > 0:
            source_counts: dict[str, int] = {}
            for it in stage1_accepted_items:
                ev = dict(it.get("evidence_span") or {})
                source = str(ev.get("source_file") or "").strip() or "(missing_source)"
                source_counts[source] = int(source_counts.get(source) or 0) + 1
            stage1_dominant_source, dominant_count = max(source_counts.items(), key=lambda kv: kv[1])
            stage1_max_source_share = dominant_count / max(1, stage1_total)
            if (
                stage1_total >= args.min_stage1_samples
                and len(source_counts) >= args.min_distinct_stage1_sources
                and stage1_max_source_share > args.max_stage1_source_share
            ):
                slug_issues.append(
                    f"stage1 source concentration too high {stage1_max_source_share:.3f} > {args.max_stage1_source_share:.3f} (source={stage1_dominant_source}, {dominant_count}/{stage1_total})"
                )

        for s_issue in slug_issues:
            issues.append(f"{slug}: {s_issue}")
        slug_metrics.append(
            {
                "slug": slug,
                "items_total": total,
                "candidate_items_total": len(items),
                "signal_items_total": len(signal_items),
                "contract_coverage": round(contract_coverage, 6),
                "high_confidence_rate": round(high_confidence_rate, 6),
                "unknown_rate": round(unknown_rate, 6),
                "branch_integrity": round(integrity, 6),
                "stage1_accepted_total": stage1_total,
                "stage1_dominant_source": stage1_dominant_source,
                "stage1_max_source_share": round(stage1_max_source_share, 6),
                "issues": slug_issues,
            }
        )

    report_payload = {
        "root_id": root_id,
        "checked_confirmed_slugs": checked,
        "issues_total": len(issues),
        "thresholds": {
            "min_items_for_rate": args.min_items_for_rate,
            "min_signal_for_unknown": args.min_signal_for_unknown,
            "min_contract_coverage": args.min_contract_coverage,
            "min_high_confidence_rate": args.min_high_confidence_rate,
            "max_unknown_rate": args.max_unknown_rate,
            "min_branch_integrity": args.min_branch_integrity,
            "min_stage1_samples": args.min_stage1_samples,
            "min_distinct_stage1_sources": args.min_distinct_stage1_sources,
            "max_stage1_source_share": args.max_stage1_source_share,
        },
        "slug_metrics": slug_metrics,
        "issues": issues,
    }
    _write_reports(curated_root, str(args.report_json or "").strip(), str(args.report_md or "").strip(), report_payload)

    if issues:
        print("S3 quality issues:", file=sys.stderr)
        for msg in issues:
            print(f"  {msg}", file=sys.stderr)
    print(f"S3 quality check: checked_confirmed_slugs={checked} issues={len(issues)}")
    if issues and not args.warn_only:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
