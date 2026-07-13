#!/usr/bin/env python3
"""Check proposition artifacts for confirmed themes (S3.5 gate)."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

_SCRIPTS = next(p for p in Path(__file__).resolve().parents if (p / "_install.py").is_file())
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
import _install

_install.bootstrap(__file__)

from proposition_policy import load_policy_bundle, resolve_base_policy, resolve_intent_policy
from distill.structured_source import structured_source_signal
from runtime.domain_knowledge_paths import CURATED_BY_ROOT, confirmed_slugs_from_checklist, resolve_checklist_file


def _load_policy_bundle() -> tuple[dict[str, object], str]:
    cfg_path = Path(__file__).with_name("proposition_policy_config.json")
    return load_policy_bundle(cfg_path), os.environ.get("KB_TEAM", "").strip()


_POLICY_BUNDLE, _POLICY_TEAM = _load_policy_bundle()
_POLICY_CONFIG = resolve_base_policy(_POLICY_BUNDLE, team=_POLICY_TEAM)
VALID_DOC_INTENTS = {"rule_spec"} | {
    str(it.get("intent") or "").strip()
    for it in list(_POLICY_CONFIG.get("doc_intent_patterns") or [])
    if str(it.get("intent") or "").strip()
}
VALID_CANDIDATE_TYPES = {
    str(x).strip()
    for x in list(_POLICY_CONFIG.get("candidate_types") or ["contract_candidate", "evidence_note"])
    if str(x).strip()
}
_INTENT_GATE = dict(_POLICY_CONFIG.get("intent_gate") or {})
_EXTRACT_EFFECTIVENESS_GATE = dict(_POLICY_CONFIG.get("extract_effectiveness_gate") or {})
_CAUSALITY_GATE = dict(_POLICY_CONFIG.get("causality_gate") or {})
_ADMISSION_MODEL = dict(_POLICY_CONFIG.get("admission_model") or {})
_ADMISSION_ANTI_FN_GATE = dict(_ADMISSION_MODEL.get("anti_false_negative_gate") or {})
_ADMISSION_DISTRIBUTION_GUARD = dict(_ADMISSION_MODEL.get("distribution_guard") or {})
_ARROW_RE = re.compile(r"(?:->|→|=>)")
_STATUS_TRANSITION_RE = re.compile(r"状态\s*变为")
_UNRESOLVED_RE = re.compile(r"(未确定|待确认|待定|unknown|tbd)", re.IGNORECASE)
VALID_DECISION_TRACKS = {"decision_core", "presentation_context", "unresolved_critical", "noise_context"}
PRESERVED_SEMANTIC_ROLES = {
    "named_business_structure",
    "branch_marker",
    "threshold_anchor",
    "condition_or_rule_cue",
    "outcome_cue",
    "unresolved_marker",
}


def _intent_gate_for(doc_intent: str) -> dict[str, object]:
    effective = resolve_intent_policy(_POLICY_BUNDLE, intent=doc_intent, team=_POLICY_TEAM)
    gate = dict(effective.get("intent_gate") or {})
    return _INTENT_GATE if not gate else gate


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate S3.5 proposition artifacts.")
    parser.add_argument("--root-id", required=True, help="Confluence root page ID")
    parser.add_argument(
        "--min-pages-with-props",
        type=int,
        default=1,
        help="Minimum number of pages with proposition candidates per confirmed slug",
    )
    parser.add_argument("--warn-only", action="store_true", help="Print issues but exit 0")
    return parser.parse_args()


def _confirmed_slugs(text: str) -> list[str]:
    return confirmed_slugs_from_checklist(text)


def _source_has_structured_signal(page: dict[str, object]) -> bool:
    materialized_file = str(page.get("materialized_file") or "").strip()
    if not materialized_file:
        return False
    path = Path(__file__).resolve().parents[2] / materialized_file
    if not path.is_file():
        return False
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return bool(structured_source_signal(text).get("has_structured_source"))


def main() -> int:
    args = _parse_args()
    root_id = str(args.root_id).strip()
    curated_root = CURATED_BY_ROOT / root_id
    checklist = resolve_checklist_file(curated_root)
    if checklist is None:
        print(f"Missing checklist: {curated_root / 'DOMAIN_MODULE_CHECKLIST.md'}", file=sys.stderr)
        return 0 if args.warn_only else 1

    slugs = _confirmed_slugs(checklist.read_text(encoding="utf-8", errors="replace"))
    issues: list[str] = []
    checked = 0
    for slug in slugs:
        checked += 1
        agg_dir = curated_root / "_aggregate" / slug
        json_path = agg_dir / f"{slug}-propositions.json"
        md_path = agg_dir / f"{slug}-命题清单.md"
        if not json_path.is_file():
            issues.append(f"{json_path}: missing proposition json")
            continue
        if not md_path.is_file():
            issues.append(f"{md_path}: missing proposition markdown")
        try:
            payload = json.loads(json_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            issues.append(f"{json_path}: invalid json ({e})")
            continue
        pages_with_props = int(payload.get("pages_with_props") or 0)
        if pages_with_props < args.min_pages_with_props:
            issues.append(
                f"{json_path}: pages_with_props={pages_with_props} < {args.min_pages_with_props}"
            )
        items: list[dict[str, object]] = []
        eff_counts: dict[str, int] = {
            "arrow_total": 0,
            "arrow_good": 0,
            "status_total": 0,
            "status_good": 0,
            "unresolved_total": 0,
            "unresolved_good": 0,
        }
        causality_counts: dict[str, int] = {
            "track_total": 0,
            "decision_core": 0,
            "unresolved_total": 0,
            "unresolved_exposed": 0,
            "high_causal_total": 0,
            "high_causal_miss": 0,
        }
        stage1_dist: dict[str, dict[str, int] | int] = {
            "total": 0,
            "by_source": {},
            "by_intent": {},
        }
        for page in list(payload.get("pages") or []):
            page_items = list(page.get("proposition_items") or [])
            items.extend(page_items)
            doc_intent = str(page.get("doc_intent") or "").strip()
            intent_conf = int(page.get("doc_intent_confidence") or 0)
            if _source_has_structured_signal(page) and not dict(page.get("structured_source") or {}).get(
                "has_structured_source"
            ):
                issues.append(f"{json_path}: structured source signal not materialized for {page.get('materialized_file')}")
            if doc_intent not in VALID_DOC_INTENTS:
                issues.append(f"{json_path}: invalid doc_intent={doc_intent or '(missing)'}")
            page_scope_markers = list(page.get("scope_markers") or [])
            page_scope_ids = {
                str(m.get("scope_id") or "").strip()
                for m in page_scope_markers
                if str(m.get("scope_id") or "").strip()
            }
            marker_branch_ids = {
                str(t).strip()
                for m in page_scope_markers
                for t in list(dict(m).get("branch_ids") or [])
                if str(t).strip()
            }
            if page_scope_markers and not page_scope_ids:
                issues.append(f"{json_path}: scope_markers present but no valid scope_id")
            if page_scope_ids and page_items:
                item_scope_ids = {
                    str(it.get("scope_id") or "").strip()
                    for it in page_items
                    if str(it.get("scope_id") or "").strip()
                }
                uncovered = sorted(s for s in page_scope_ids if s not in item_scope_ids)
                if uncovered:
                    issues.append(
                        f"{json_path}: scope markers uncovered by items ({', '.join(uncovered)})"
                    )
            contract_count = 0
            evidence_count = 0
            for it in page_items:
                text = str(it.get("text") or "")
                block = dict(it.get("decision_block") or {})
                cond = str(block.get("condition") or "").strip()
                action = str(block.get("action") or "").strip()
                outcome = str(block.get("observable_outcome") or "").strip()
                exc = str(block.get("exception") or "").strip()
                candidate_type = str(it.get("candidate_type") or "").strip()
                eligibility_reason = str(it.get("eligibility_reason") or "").strip()
                decision_track = str(it.get("decision_track") or "").strip()
                semantic_roles = {
                    str(x).strip()
                    for x in list(it.get("semantic_roles") or [])
                    if str(x).strip()
                }
                semantic_preservation_reason = str(it.get("semantic_preservation_reason") or "").strip()
                business_scope_label = str(
                    it.get("business_scope_label") or it.get("semantic_scope_label") or ""
                ).strip()
                admission_stage1_result = str(it.get("admission_stage1_result") or "").strip()
                admission_drop_reason = str(it.get("admission_drop_reason") or "").strip()
                causality_score = int(it.get("causality_score") or 0)
                item_doc_intent = str(it.get("doc_intent") or "").strip()
                if candidate_type not in VALID_CANDIDATE_TYPES:
                    issues.append(
                        f"{json_path}: invalid candidate_type on proposition ({text[:80]})"
                    )
                if not eligibility_reason:
                    issues.append(
                        f"{json_path}: missing eligibility_reason on proposition ({text[:80]})"
                    )
                if item_doc_intent != doc_intent:
                    issues.append(
                        f"{json_path}: page/item doc_intent mismatch ({doc_intent} != {item_doc_intent or '(missing)'})"
                    )
                if decision_track not in VALID_DECISION_TRACKS:
                    issues.append(
                        f"{json_path}: invalid decision_track on proposition ({text[:80]})"
                    )
                if not semantic_roles:
                    issues.append(
                        f"{json_path}: missing semantic_roles on proposition ({text[:80]})"
                    )
                if not semantic_preservation_reason:
                    issues.append(
                        f"{json_path}: missing semantic_preservation_reason on proposition ({text[:80]})"
                    )
                if not business_scope_label:
                    issues.append(
                        f"{json_path}: missing business_scope_label on proposition ({text[:80]})"
                    )
                if candidate_type == "noise_context" and PRESERVED_SEMANTIC_ROLES.intersection(semantic_roles):
                    issues.append(
                        f"{json_path}: preserved business semantics isolated as noise ({text[:80]})"
                    )
                if not admission_stage1_result:
                    issues.append(
                        f"{json_path}: missing admission stage1 field ({text[:80]})"
                    )
                if candidate_type == "noise_context" and not admission_drop_reason:
                    issues.append(
                        f"{json_path}: noise item missing admission_drop_reason ({text[:80]})"
                    )
                if candidate_type == "contract_candidate":
                    contract_count += 1
                else:
                    evidence_count += 1
                if decision_track in VALID_DECISION_TRACKS and candidate_type == "contract_candidate":
                    causality_counts["track_total"] += 1
                    if decision_track == "decision_core":
                        causality_counts["decision_core"] += 1
                    if _UNRESOLVED_RE.search(text):
                        causality_counts["unresolved_total"] += 1
                        if decision_track == "unresolved_critical":
                            causality_counts["unresolved_exposed"] += 1
                anti_fn_tracks = {
                    str(x).strip()
                    for x in list(_ADMISSION_ANTI_FN_GATE.get("tracks") or ["decision_core", "unresolved_critical"])
                    if str(x).strip()
                }
                if (
                    decision_track in anti_fn_tracks
                    and causality_score >= int(_ADMISSION_ANTI_FN_GATE.get("min_causality_score") or 8)
                ):
                    causality_counts["high_causal_total"] += 1
                    if candidate_type != "contract_candidate":
                        causality_counts["high_causal_miss"] += 1
                scope_id = str(it.get("scope_id") or "").strip()
                scope_label = str(it.get("scope_label") or "").strip()
                if not scope_id or not scope_label:
                    issues.append(
                        f"{json_path}: missing scope fields on proposition ({text[:80]})"
                    )
                ev = dict(it.get("evidence_span") or {})
                source_file = str(ev.get("source_file") or "").strip()
                start_line = int(ev.get("start_line") or 0)
                end_line = int(ev.get("end_line") or 0)
                if not source_file or start_line <= 0 or end_line <= 0 or end_line < start_line:
                    issues.append(
                        f"{json_path}: invalid evidence_span on proposition ({text[:80]})"
                    )
                if admission_stage1_result == "accepted":
                    stage1_dist["total"] = int(stage1_dist.get("total") or 0) + 1
                    by_source = dict(stage1_dist.get("by_source") or {})
                    by_intent = dict(stage1_dist.get("by_intent") or {})
                    source_key = source_file or "(missing_source)"
                    by_source[source_key] = int(by_source.get(source_key) or 0) + 1
                    intent_key = item_doc_intent or "(missing_intent)"
                    by_intent[intent_key] = int(by_intent.get(intent_key) or 0) + 1
                    stage1_dist["by_source"] = by_source
                    stage1_dist["by_intent"] = by_intent
                tags = {str(x).strip() for x in list(it.get("branch_ids") or [])}
                # If page has explicit scope markers, branch-tagged items should bind to a non-global scope.
                if marker_branch_ids and tags and scope_id == "global":
                    issues.append(
                        f"{json_path}: branch-tagged item stayed in global scope ({text[:80]})"
                    )
                if _ARROW_RE.search(text) and ("是否" in text or "?" in text or "？" in text):
                    eff_counts["arrow_total"] += 1
                    if cond and (outcome or action):
                        eff_counts["arrow_good"] += 1
                if _STATUS_TRANSITION_RE.search(text):
                    eff_counts["status_total"] += 1
                    if _STATUS_TRANSITION_RE.search(action) or _STATUS_TRANSITION_RE.search(outcome):
                        eff_counts["status_good"] += 1
                if _UNRESOLVED_RE.search(text) and decision_track != "presentation_context":
                    eff_counts["unresolved_total"] += 1
                    if _UNRESOLVED_RE.search(exc) or _UNRESOLVED_RE.search(outcome):
                        eff_counts["unresolved_good"] += 1
            page_total = contract_count + evidence_count
            gate = _intent_gate_for(doc_intent)
            min_page_total_for_ratio = int(gate.get("min_page_total_for_ratio") or 4)
            if page_total >= min_page_total_for_ratio:
                contract_ratio = contract_count / page_total
                release_like_intents = {
                    str(x).strip()
                    for x in list(gate.get("release_like_intents") or ["release_change", "test_ops"])
                    if str(x).strip()
                }
                # Hard fail only on high-confidence engineering pages with heavy contract leakage.
                if (
                    doc_intent in release_like_intents
                    and intent_conf >= int(gate.get("release_confidence_min") or 3)
                    and page_total >= int(gate.get("release_page_total_min") or 10)
                    and contract_ratio > float(gate.get("release_contract_ratio_max") or 0.60)
                ):
                    issues.append(
                        f"{json_path}: {doc_intent} page contract leakage too high ({contract_count}/{page_total})"
                    )
                # Hard fail only when title strongly indicates a rule page.
                if (
                    doc_intent == "rule_spec"
                    and intent_conf >= int(gate.get("rule_confidence_min") or 3)
                    and page_total >= int(gate.get("rule_page_total_min") or 8)
                    and contract_ratio < float(gate.get("rule_contract_ratio_min") or 0.20)
                ):
                    issues.append(
                        f"{json_path}: rule_spec page contract density too low ({contract_count}/{page_total})"
                    )
        if bool(_EXTRACT_EFFECTIVENESS_GATE.get("enabled", True)):
            arrow_cfg = dict(_EXTRACT_EFFECTIVENESS_GATE.get("arrow_qa") or {})
            status_cfg = dict(_EXTRACT_EFFECTIVENESS_GATE.get("status_transition") or {})
            unresolved_cfg = dict(_EXTRACT_EFFECTIVENESS_GATE.get("unresolved_capture") or {})

            arrow_total = int(eff_counts["arrow_total"])
            if arrow_total >= int(arrow_cfg.get("min_samples") or 2):
                arrow_rate = float(eff_counts["arrow_good"]) / float(arrow_total)
                if arrow_rate < float(arrow_cfg.get("min_rate") or 0.5):
                    issues.append(
                        f"{json_path}: arrow_qa_parse_rate too low ({eff_counts['arrow_good']}/{arrow_total})"
                    )

            status_total = int(eff_counts["status_total"])
            if status_total >= int(status_cfg.get("min_samples") or 2):
                status_rate = float(eff_counts["status_good"]) / float(status_total)
                if status_rate < float(status_cfg.get("min_rate") or 0.6):
                    issues.append(
                        f"{json_path}: status_transition_parse_rate too low ({eff_counts['status_good']}/{status_total})"
                    )

            unresolved_total = int(eff_counts["unresolved_total"])
            if unresolved_total >= int(unresolved_cfg.get("min_samples") or 2):
                unresolved_rate = float(eff_counts["unresolved_good"]) / float(unresolved_total)
                if unresolved_rate < float(unresolved_cfg.get("min_rate") or 0.7):
                    issues.append(
                        f"{json_path}: unresolved_capture_rate too low ({eff_counts['unresolved_good']}/{unresolved_total})"
                    )
        if bool(_CAUSALITY_GATE.get("enabled", True)):
            total = int(causality_counts["track_total"])
            core_total = int(causality_counts["decision_core"])
            unresolved_total = int(causality_counts["unresolved_total"])
            unresolved_exposed = int(causality_counts["unresolved_exposed"])

            if total >= int(_CAUSALITY_GATE.get("decision_core_min_samples") or 8):
                core_ratio = float(core_total) / float(total)
                if core_ratio < float(_CAUSALITY_GATE.get("decision_core_min_ratio") or 0.2):
                    issues.append(f"{json_path}: decision_core_ratio too low ({core_total}/{total})")
            if unresolved_total >= int(_CAUSALITY_GATE.get("unresolved_critical_min_samples") or 2):
                unresolved_ratio = float(unresolved_exposed) / float(unresolved_total)
                if unresolved_ratio < float(_CAUSALITY_GATE.get("unresolved_exposed_min_ratio") or 0.8):
                    issues.append(
                        f"{json_path}: unresolved_exposed_ratio too low ({unresolved_exposed}/{unresolved_total})"
                    )
        if bool(_ADMISSION_ANTI_FN_GATE.get("enabled", True)):
            high_total = int(causality_counts["high_causal_total"])
            high_miss = int(causality_counts["high_causal_miss"])
            if high_total >= int(_ADMISSION_ANTI_FN_GATE.get("min_samples") or 3):
                miss_rate = float(high_miss) / float(high_total)
                if miss_rate > float(_ADMISSION_ANTI_FN_GATE.get("max_high_causality_miss_rate") or 0.35):
                    issues.append(
                        f"{json_path}: high_causality_miss_rate too high ({high_miss}/{high_total})"
                    )
        if bool(_ADMISSION_DISTRIBUTION_GUARD.get("enabled", True)):
            stage1_total = int(stage1_dist.get("total") or 0)
            if stage1_total >= int(_ADMISSION_DISTRIBUTION_GUARD.get("min_stage1_samples") or 12):
                by_source = dict(stage1_dist.get("by_source") or {})
                by_intent = dict(stage1_dist.get("by_intent") or {})
                if len(by_source) >= int(_ADMISSION_DISTRIBUTION_GUARD.get("min_distinct_stage1_sources") or 2):
                    src_name, src_count = max(by_source.items(), key=lambda kv: kv[1])
                    src_share = float(src_count) / float(stage1_total)
                    if src_share > float(_ADMISSION_DISTRIBUTION_GUARD.get("max_single_source_share") or 0.7):
                        issues.append(
                            f"{json_path}: stage1 concentration too high on one source ({src_count}/{stage1_total}, source={src_name})"
                        )
                if len(by_intent) >= int(_ADMISSION_DISTRIBUTION_GUARD.get("min_distinct_stage1_intents") or 2):
                    intent_name, intent_count = max(by_intent.items(), key=lambda kv: kv[1])
                    intent_share = float(intent_count) / float(stage1_total)
                    if intent_share > float(_ADMISSION_DISTRIBUTION_GUARD.get("max_single_intent_share") or 0.85):
                        issues.append(
                            f"{json_path}: stage1 concentration too high on one intent ({intent_count}/{stage1_total}, intent={intent_name})"
                        )
        if items:
            signal_items = []
            for it in items:
                text = str(it.get("text") or "")
                tags = list(it.get("branch_ids") or [])
                if tags or re.search(r"\d", text) or re.search(r"(当|如果|if|when|状态|资格|奖励|结算|支付|展示|可见)", text, re.IGNORECASE):
                    signal_items.append(it)
            contract_signal_items = [
                it for it in signal_items if str(it.get("candidate_type") or "") == "contract_candidate"
            ]
            good_blocks = 0
            low_info_blocks = 0
            b1, b2 = 0, 0
            for it in contract_signal_items:
                conf = int(it.get("decision_confidence") or 0)
                block = dict(it.get("decision_block") or {})
                non_empty = int(it.get("decision_fields_count") or 0)
                if non_empty <= 0:
                    non_empty = sum(1 for v in block.values() if str(v).strip())
                if conf >= 4 and non_empty >= 3:
                    good_blocks += 1
                if conf <= 1 and non_empty <= 1:
                    low_info_blocks += 1
            for it in signal_items:
                tags = {str(x).strip() for x in list(it.get("branch_ids") or [])}
                if "branch_1" in tags:
                    b1 += 1
                if "branch_2" in tags:
                    b2 += 1
            if len(contract_signal_items) >= 20 and good_blocks < max(2, len(contract_signal_items) // 20):
                issues.append(
                    f"{json_path}: low high-confidence decision blocks ({good_blocks}/{len(contract_signal_items)})"
                )
            if len(contract_signal_items) >= 20 and (low_info_blocks / len(contract_signal_items)) > 0.70:
                issues.append(
                    f"{json_path}: low-information signal items too high ({low_info_blocks}/{len(contract_signal_items)})"
                )
            explicit_b1 = any(
                re.search(r"(挑战一|第一阶段|branch\s*1|phase\s*1|challenge\s*one|1st\s*challenge)", str(it.get("text") or ""), re.IGNORECASE)
                for it in signal_items
            )
            explicit_b2 = any(
                re.search(r"(挑战二|第二阶段|branch\s*2|phase\s*2|challenge\s*two|2nd\s*challenge)", str(it.get("text") or ""), re.IGNORECASE)
                for it in signal_items
            )
            if explicit_b1 and explicit_b2:
                if b1 == 0 or b2 == 0:
                    issues.append(f"{json_path}: explicit dual-branch context but branch ids missing (b1={b1}, b2={b2})")
                elif (b1 + b2) >= 8 and (min(b1, b2) / max(b1, b2)) < 0.25:
                    issues.append(f"{json_path}: branch extraction asymmetry too high (b1={b1}, b2={b2})")

    if issues:
        print("Proposition quality issues:", file=sys.stderr)
        for msg in issues:
            print(f"  {msg}", file=sys.stderr)
    print(f"Proposition quality check: checked_confirmed_slugs={checked} issues={len(issues)}")
    if issues and not args.warn_only:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
