#!/usr/bin/env python3
"""Build per-page proposition candidates for confirmed themes (S3.5)."""
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

from _bootstrap import REPO_ROOT
from proposition_policy import load_policy_bundle, resolve_base_policy
from structured_source import structured_source_signal
from runtime.domain_knowledge_paths import (
    CHECKLIST_STATUS_CONFIRMED,
    is_checklist_status_confirmed,
    CURATED_BY_ROOT,
    MATERIALIZED_BY_ROOT,
    resolve_checklist_file,
)
from runtime.rule_phase import classify_rule_text

CHECKLIST_SLUG_RE = re.compile(r"（([^）]+)）")
_DELIVER_SLUG_RE = re.compile(r"_deliver/([a-z0-9-]+)/")


def _slug_from_checklist_row(cols: list[str]) -> str | None:
    """Prefer _deliver/<slug>/ in 主入口; else last （slug） in 主题."""
    if len(cols) >= 4:
        m = _DELIVER_SLUG_RE.search(cols[3])
        if m:
            return m.group(1)
    if cols:
        matches = CHECKLIST_SLUG_RE.findall(cols[0])
        if matches:
            return matches[-1].strip()
    return None


def _theme_cn_from_row(theme: str, slug: str) -> str:
    suffix = f"（{slug}）"
    if theme.endswith(suffix):
        return theme[: -len(suffix)].strip()
    return CHECKLIST_SLUG_RE.sub("", theme).strip()
TITLE_URL_RE = re.compile(r"^###\s+\[(.+?)\]\((https?://[^)]+)\)")
ANCHOR_RE = re.compile(
    r"(`[^`]+`|"
    r"\d+\s*(?:%|天|周|月|年|小时|分钟)|"
    r"\b(?:if|when|must|should|cannot|only|unless|status|state|limit|threshold)\b|"
    r"(?:如果|当|仅当|必须|不得|不可|上限|下限|阈值|时限|状态|成功|失败|取消|例外|否则)|"
    r"/[A-Za-z0-9_\-{}$]+|"
    r"\b[A-Z]{2,}(?:_[A-Z0-9]+)*\b)",
    re.IGNORECASE,
)
NUMERIC_ANCHOR_RE = re.compile(
    r"\d+(?:,\d{3})*(?:\.\d+)?\s*(?:%|天|周|月|年|小时|分钟|CVP|SVP|FPV|CNY|¥)?",
    re.IGNORECASE,
)
BUSINESS_SIGNAL_RE = re.compile(
    r"(如果|当|仅当|必须|不得|不可|上限|下限|阈值|时限|状态|成功|失败|取消|例外|否则|"
    r"资格|达标|晋升|奖励|奖金|支付|下单|可见|隐藏|审核|结算|报名|发放)",
    re.IGNORECASE,
)
ACTOR_RE = re.compile(r"(顾问|用户|会员|运营|客户|customer|consultant|user|operator)", re.IGNORECASE)
CONDITION_RE = re.compile(
    r"(?:当|如果|若|仅当|when|if)\s*(.+?)(?:，|,|则|then|可|会|将|进入|获得|显示|触发)",
    re.IGNORECASE,
)
ACTION_RE = re.compile(
    r"(?:则|then|会|将|进入|触发|发放|展示|显示|可以|可在)\s*(.+)$",
    re.IGNORECASE,
)
OUTCOME_RE = re.compile(
    r"(获得|发放|入账|展示|显示|可见|不可见|通过|拒绝|成功|失败|达成|未达成|状态|隐藏|倒计时)",
    re.IGNORECASE,
)
CAUSAL_OUTCOME_RE = re.compile(
    r"(receive|award|reward|rewards|dividend|dividends|bonus|activate|activated|"
    r"eligible|ineligible|approved|rejected|allow|deny|"
    r"通过|拒绝|发放|奖励|入账|生效|失效|激活|达标|未达成|晋升|结算|支付成功|支付失败|状态\s*变为|迁移)",
    re.IGNORECASE,
)
TIME_RE = re.compile(r"(\d+\s*(?:天|周|月|年)|周期|窗口|截至|起始|结束|倒计时)", re.IGNORECASE)
EXCEPTION_RE = re.compile(r"(例外|除外|除非|unless|except)", re.IGNORECASE)
UNRESOLVED_RE = re.compile(r"(未确定|待确认|待定|unknown|tbd)", re.IGNORECASE)
ENGINEERING_NOISE_RE = re.compile(
    r"(bugfix|jira|dev-\d+|sql|ddl|repository|repo|codebase|project\s*manager|endpoint\s*:|service\s*:|"
    r"@[\w\-.]+|[\w\-.]+@[\w\-.]+\.\w+)",
    re.IGNORECASE,
)
NOISE_LINE_RE = re.compile(
    r"([a-f0-9]{24,}|[0-9a-f]{8}-[0-9a-f\-]{18,}|v2_[a-f0-9]{16,}|"
    r"[A-Za-z0-9_\-]{64,}|^\s*\d+\s+[a-f0-9\-]{8,})",
    re.IGNORECASE,
)
BRANCH_ANCHOR_RE = re.compile(
    r"(挑战一|挑战二|第一阶段|第二阶段|branch\s*[12]|phase\s*[12]|"
    r"challenge\s*(?:one|two|1|2)|1st\s*challenge|2nd\s*challenge)",
    re.IGNORECASE,
)
NAMED_BUSINESS_STRUCTURE_RE = re.compile(
    r"(challenge|phase|stage|branch|tier|level|milestone|bonus|campaign|promotion|contest|"
    r"eligibility|settlement|reward|payout|dividend|status|workflow|scenario|case|route|"
    r"挑战|阶段|分支|层级|等级|里程碑|奖金|激励|活动|促销|竞赛|资格|结算|发放|分红|状态|流程|场景|路径)",
    re.IGNORECASE,
)
DECISION_CUE_RE = re.compile(
    r"(如果|当|若|仅当|除非|否则|则|必须|不得|可|会|将|资格|达标|奖励|结算|发放|"
    r"\bif\b|\bwhen\b|\bthen\b|\bunless\b|\bonly\b|\bmust\b|\bshould\b|\bcan\b|\bwill\b)",
    re.IGNORECASE,
)
DEPENDENCY_HINTS: list[tuple[str, re.Pattern[str], list[str]]] = [
    ("payment", re.compile(r"(支付|回写|payment|订单状态)", re.IGNORECASE), ["precheck", "adjudication"]),
    ("settlement", re.compile(r"(结算|发放|入账)", re.IGNORECASE), ["eligibility", "adjudication"]),
    ("presentation", re.compile(r"(展示|列表|卡片|弹窗|report|analytics)", re.IGNORECASE), ["eligibility", "adjudication"]),
]

def _load_policy_bundle() -> tuple[dict[str, object], str]:
    cfg_path = Path(__file__).with_name("proposition_policy_config.json")
    return load_policy_bundle(cfg_path), os.environ.get("KB_TEAM", "").strip()


_POLICY_BUNDLE, _POLICY_TEAM = _load_policy_bundle()
_POLICY_CONFIG = resolve_base_policy(_POLICY_BUNDLE, team=_POLICY_TEAM)
DOC_INTENT_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (str(it.get("intent") or "").strip(), re.compile(str(it.get("pattern") or ""), re.IGNORECASE))
    for it in list(_POLICY_CONFIG.get("doc_intent_patterns") or [])
    if str(it.get("intent") or "").strip() and str(it.get("pattern") or "").strip()
]
_CANDIDATE_PATTERNS = dict(_POLICY_CONFIG.get("candidate_patterns") or {})
RULE_SIGNAL_RE = re.compile(
    str(_CANDIDATE_PATTERNS.get("rule_signal") or r"$^"),
    re.IGNORECASE,
)
OUTCOME_SIGNAL_RE = re.compile(
    str(_CANDIDATE_PATTERNS.get("outcome_signal") or r"$^"),
    re.IGNORECASE,
)
_ADMISSION_MODEL = dict(_POLICY_CONFIG.get("admission_model") or {})
_SEMANTIC_RETENTION = dict(_ADMISSION_MODEL.get("semantic_retention") or {})
_PRESENTATION_CUE_RE = re.compile(r"(显示|展示|卡片|列表|弹窗|文案|高亮|置灰|status\s*bar|ui|page)", re.IGNORECASE)


def _infer_phase(text: str) -> str:
    return classify_rule_text(text)


def _infer_dependencies(text: str, phase: str) -> list[str]:
    deps: list[str] = []
    for _name, patt, expected in DEPENDENCY_HINTS:
        if patt.search(text):
            deps.extend(expected)
    if phase == "placeholder":
        return []
    if phase == "precheck":
        deps.append("eligibility")
    if phase == "settlement":
        deps.extend(["eligibility", "adjudication"])
    if phase == "presentation":
        deps.extend(["eligibility", "adjudication"])
    ordered: list[str] = []
    for dep in deps:
        if dep not in ordered and dep != phase:
            ordered.append(dep)
    return ordered


def _detect_doc_intent(title: str, lines: list[str]) -> tuple[str, int]:
    title_text = str(title or "")
    sample = " ".join(lines[:80])
    bag = f"{title_text}\n{sample}"
    for intent, patt in DOC_INTENT_PATTERNS:
        score = len(patt.findall(bag))
        if score > 0:
            return intent, score
    return "rule_spec", 0


def _rule_signal_strength(text: str) -> int:
    score = 0
    if RULE_SIGNAL_RE.search(text):
        score += 1
    if OUTCOME_SIGNAL_RE.search(text) or OUTCOME_RE.search(text):
        score += 1
    if re.search(r"\d", text):
        score += 1
    if re.search(r"(if|when|unless|only|must|should)", text, re.IGNORECASE):
        score += 1
    if re.search(r"(如果|当|仅当|除非|必须|不得|否则)", text):
        score += 1
    return score


def _admission_thresholds_for_intent(doc_intent: str) -> dict[str, object]:
    stage1 = dict(_ADMISSION_MODEL.get("stage1") or {})
    overrides = dict((_ADMISSION_MODEL.get("stage1_by_intent") or {}).get(doc_intent) or {})
    merged = dict(stage1)
    merged.update(overrides)
    return merged


def _semantic_roles(text: str, block: dict[str, str], tags: list[str]) -> list[str]:
    roles: list[str] = []
    if NAMED_BUSINESS_STRUCTURE_RE.search(text):
        roles.append("named_business_structure")
    if tags or BRANCH_ANCHOR_RE.search(text):
        roles.append("branch_marker")
    if NUMERIC_ANCHOR_RE.search(text):
        roles.append("threshold_anchor")
    if DECISION_CUE_RE.search(text) or str(block.get("condition") or "").strip():
        roles.append("condition_or_rule_cue")
    if OUTCOME_RE.search(text) or str(block.get("observable_outcome") or "").strip():
        roles.append("outcome_cue")
    if TIME_RE.search(text) or str(block.get("time_window") or "").strip():
        roles.append("time_window")
    if EXCEPTION_RE.search(text) or str(block.get("exception") or "").strip():
        roles.append("exception_cue")
    if UNRESOLVED_RE.search(text):
        roles.append("unresolved_marker")
    if _PRESENTATION_CUE_RE.search(text):
        roles.append("presentation_cue")
    if ENGINEERING_NOISE_RE.search(text) or NOISE_LINE_RE.search(text):
        roles.append("noise_cue")
    if not roles and ANCHOR_RE.search(text):
        roles.append("source_anchor")
    return list(dict.fromkeys(roles))


def _semantic_preservation_reason(roles: list[str], decision_track: str, candidate_type: str) -> str:
    if decision_track == "noise_context":
        return "isolated_as_noise_without_business_decision_value"
    if "unresolved_marker" in roles:
        return "preserved_for_delayed_unresolved_decision"
    if "branch_marker" in roles or "named_business_structure" in roles:
        return "preserved_named_business_structure"
    if "threshold_anchor" in roles and (
        "condition_or_rule_cue" in roles or "outcome_cue" in roles
    ):
        return "preserved_threshold_rule_semantics"
    if candidate_type == "contract_candidate":
        return "preserved_as_contract_candidate"
    return "preserved_as_evidence_for_agent_judgment"


def _should_force_semantic_retention(text: str, tags: list[str], score: int) -> bool:
    if not bool(_SEMANTIC_RETENTION.get("enabled", True)):
        return False
    roles = _semantic_roles(text, {}, tags)
    force_roles = {
        str(x).strip()
        for x in list(
            _SEMANTIC_RETENTION.get("force_roles")
            or ["named_business_structure", "branch_marker", "unresolved_marker", "threshold_anchor"]
        )
        if str(x).strip()
    }
    if not force_roles.intersection(roles):
        return False
    if "threshold_anchor" in roles and bool(_SEMANTIC_RETENTION.get("require_signal_for_threshold", True)):
        return "condition_or_rule_cue" in roles or "outcome_cue" in roles or score >= 3
    if "noise_cue" in roles and not {"condition_or_rule_cue", "outcome_cue", "unresolved_marker"}.intersection(roles):
        return False
    return True


def _business_scope_label(text: str, scope_label: str, tags: list[str], roles: list[str]) -> str:
    if scope_label and scope_label != "global":
        return scope_label
    if tags:
        return " / ".join(tags)
    if "named_business_structure" in roles:
        m = NAMED_BUSINESS_STRUCTURE_RE.search(text)
        if m:
            return m.group(0)
    return "global"


def _admit_candidate(
    doc_intent: str,
    text: str,
    confidence: int,
    non_empty_fields: int,
    signal: int,
    decision_track: str,
    causality_score: int,
) -> tuple[str, str, dict[str, object]]:
    _ = text
    if not bool(_ADMISSION_MODEL.get("enabled", True)):
        return "evidence_note", "admission_model_disabled", {
            "stage1_result": "bypassed",
            "stage1_reason": "admission_model_disabled",
            "risk_flags": [],
            "final_reason": "admission_model_disabled",
            "drop_reason": "",
        }
    if decision_track == "noise_context":
        return "noise_context", "isolated_noise_context", {
            "stage1_result": "rejected",
            "stage1_reason": "noise_context_isolated_before_contract_admission",
            "risk_flags": ["noise_context_track"],
            "final_reason": "isolated_noise_context",
            "drop_reason": "noise_without_preserved_business_semantics",
        }
    if decision_track == "presentation_context":
        return "evidence_note", "presentation_context_deferred_to_agent", {
            "stage1_result": "rejected",
            "stage1_reason": "presentation_context_deferred_to_agent",
            "risk_flags": ["presentation_context_track"],
            "final_reason": "presentation_context_deferred_to_agent",
            "drop_reason": "",
        }

    stage1_cfg = _admission_thresholds_for_intent(doc_intent)
    allow_tracks = {
        str(x).strip()
        for x in list(stage1_cfg.get("allow_tracks") or ["decision_core", "unresolved_critical"])
        if str(x).strip()
    }
    stage1_pass = (
        decision_track in allow_tracks
        and causality_score >= int(stage1_cfg.get("min_causality_score") or 8)
        and signal >= int(stage1_cfg.get("min_signal") or 3)
        and non_empty_fields >= int(stage1_cfg.get("min_fields") or 3)
    )
    stage1_result = "accepted" if stage1_pass else "rejected"
    stage1_reason = (
        "causal_admission_passed"
        if stage1_pass
        else "causal_admission_not_met"
    )
    final_type = "contract_candidate" if stage1_pass else "evidence_note"
    final_reason = "causal_admission_passed" if stage1_pass else "causal_admission_not_met"

    return final_type, final_reason, {
        "stage1_result": stage1_result,
        "stage1_reason": stage1_reason,
        "risk_flags": [],
        "final_reason": final_reason,
        "drop_reason": "",
    }


def _causality_score(
    text: str,
    block: dict[str, str],
    confidence: int,
    signal: int,
) -> int:
    score = 0
    condition = str(block.get("condition") or "").strip()
    action = str(block.get("action") or "").strip()
    outcome = str(block.get("observable_outcome") or "").strip()
    thresholds = str(block.get("thresholds") or "").strip()
    time_window = str(block.get("time_window") or "").strip()
    exception = str(block.get("exception") or "").strip()

    if condition:
        score += 2
    if action:
        score += 2
    if outcome:
        score += 2
    if thresholds:
        score += 1
    if time_window:
        score += 1
    if exception:
        score += 1
    if re.search(r"(如果|当|仅当|if|when)", text, re.IGNORECASE):
        score += 1
    if re.search(r"(则|then|->|→|=>)", text, re.IGNORECASE):
        score += 1
    score += min(max(confidence, 0), 2)
    score += 1 if signal >= 3 else 0
    return score


def _decision_track(
    text: str,
    block: dict[str, str],
    confidence: int,
    non_empty_fields: int,
    signal: int,
) -> tuple[str, str, int]:
    causality = _causality_score(text, block, confidence, signal)
    unresolved = bool(UNRESOLVED_RE.search(text)) or bool(UNRESOLVED_RE.search(str(block.get("exception") or "")))
    presentation_like = bool(_PRESENTATION_CUE_RE.search(text))
    noisy = bool(NOISE_LINE_RE.search(text)) or len(ENGINEERING_NOISE_RE.findall(text)) >= 2
    semantic_roles = _semantic_roles(text, block, [])
    has_preserved_business_semantics = bool(
        {"named_business_structure", "branch_marker", "threshold_anchor", "condition_or_rule_cue", "outcome_cue", "unresolved_marker"}.intersection(semantic_roles)
    )
    has_causal_business_outcome = bool(CAUSAL_OUTCOME_RE.search(text))
    has_core = bool(str(block.get("condition") or "").strip()) and (
        bool(str(block.get("action") or "").strip()) or bool(str(block.get("observable_outcome") or "").strip())
    )
    if noisy and not has_core and not has_preserved_business_semantics:
        return "noise_context", "noise_without_business_decision_semantics", causality
    if unresolved and (signal >= 2 or confidence >= 3 or has_core):
        return "unresolved_critical", "unresolved_high_signal_decision", causality
    if presentation_like and not has_causal_business_outcome:
        return "presentation_context", "presentation_or_display_oriented_for_deferred_judgment", causality
    if has_core and confidence >= 4 and non_empty_fields >= 3 and causality >= 7:
        return "decision_core", "causal_chain_resolved", causality
    if has_preserved_business_semantics and causality >= 5 and non_empty_fields >= 2:
        return "decision_core", "business_semantics_preserved_for_deferred_judgment", causality
    if presentation_like:
        return "presentation_context", "presentation_or_display_oriented", causality
    if causality >= 6 and non_empty_fields >= 3:
        return "decision_core", "causal_chain_partially_resolved", causality
    if noisy and not has_preserved_business_semantics:
        return "noise_context", "low_causality_noise_context", causality
    return "presentation_context", "insufficient_causal_closure", causality


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract proposition candidates by confirmed theme.")
    parser.add_argument("--root-id", required=True, help="Confluence root page ID")
    parser.add_argument(
        "--only-slug",
        action="append",
        default=[],
        help="Only process specific slug(s), repeatable",
    )
    parser.add_argument(
        "--max-lines-per-page",
        type=int,
        default=8,
        help="Max proposition candidates per source page",
    )
    parser.add_argument(
        "--allow-unconfirmed",
        action="store_true",
        help="Bypass S2 confirm gate (for emergency/manual maintenance only)",
    )
    return parser.parse_args()


def _confirmed_slugs(checklist_text: str) -> list[tuple[str, str]]:
    from runtime.checklist_modules import confirmed_slug_theme_pairs

    return confirmed_slug_theme_pairs(checklist_text)


def _has_pending_status(checklist_text: str) -> bool:
    from runtime.checklist_modules import has_pending_status

    return has_pending_status(checklist_text)


def _source_system(md_path: Path) -> str:
    rel = md_path.relative_to(REPO_ROOT).as_posix()
    if "/jira/materialized/" in f"/{rel}/":
        return "jira"
    return "confluence"


def _parse_page(md_path: Path, max_lines: int) -> dict[str, object]:
    text = md_path.read_text(encoding="utf-8", errors="replace")
    structured_signal = structured_source_signal(text)
    lines = text.splitlines()
    title = md_path.stem
    source_url = ""
    for ln in lines[:16]:
        m = TITLE_URL_RE.match(ln.strip())
        if m:
            title = m.group(1).strip()
            source_url = m.group(2).strip()
            break
    doc_intent, doc_intent_confidence = _detect_doc_intent(title, lines)

    propositions: list[str] = []
    proposition_items: list[dict[str, object]] = []
    seen: set[str] = set()
    scored_candidates: list[dict[str, object]] = []
    dropped_noise = 0
    dropped_low_signal = 0
    scope_markers: list[dict[str, object]] = []
    active_scope_id = "global"
    active_scope_label = "global"

    def _looks_engineering_noise(text: str) -> bool:
        hits = len(ENGINEERING_NOISE_RE.findall(text))
        if hits == 0:
            return False
        # Keep only strong rule-like lines even if they contain engineering tokens.
        has_rule_signal = bool(BUSINESS_SIGNAL_RE.search(text)) or bool(
            re.search(r"\b(if|when|then|can|will)\b|如果|当|则|可|会|将", text, re.IGNORECASE)
        )
        return (hits >= 2 and not has_rule_signal) or (hits >= 1 and len(text) < 80 and not has_rule_signal)

    def _normalize_branch_tag(raw: str) -> str:
        token = raw.strip().lower().replace(" ", "")
        if token in {"挑战一", "第一阶段", "branch1", "phase1"}:
            return "branch_1"
        if token in {"挑战二", "第二阶段", "branch2", "phase2"}:
            return "branch_2"
        if token in {"challengeone", "challenge1", "1stchallenge"}:
            return "branch_1"
        if token in {"challengetwo", "challenge2", "2ndchallenge"}:
            return "branch_2"
        return token

    def _extract_explicit_branch_tags(text: str) -> list[str]:
        tags: list[str] = []
        for m in BRANCH_ANCHOR_RE.finditer(text):
            tag = _normalize_branch_tag(m.group(0))
            if tag not in tags:
                tags.append(tag)
        return tags

    def _extract_branch_tags(text: str) -> list[str]:
        return _extract_explicit_branch_tags(text)

    def _is_scope_marker_line(text: str, explicit_tags: list[str]) -> bool:
        if not explicit_tags:
            return False
        normalized = re.sub(r"\s+", " ", text.strip().lower())
        if re.fullmatch(r"(challenge\s*(?:one|two|1|2)|1st\s*challenge|2nd\s*challenge)", normalized):
            return True
        if re.fullmatch(r"(挑战一|挑战二|第一阶段|第二阶段)", text.strip()):
            return True
        return False

    def _split_candidate_line(text: str) -> list[str]:
        # Preserve meaningful parallel branches from one long line.
        if len(text) < 40:
            return [text]
        if_markers = len(re.findall(r"\bif\b|如果|当", text, flags=re.IGNORECASE))
        parts = [p.strip(" ;；，,。") for p in re.split(r"[;；]", text) if p.strip(" ;；，,。")]
        if if_markers >= 2 and len(parts) >= 2:
            return parts
        # Also split long dual-if branches separated by comma for better branch atomization.
        if if_markers >= 2 and len(text) >= 80:
            comma_parts = [p.strip(" ;；，,。") for p in re.split(r"[，,](?=\s*(?:if|when|如果|当)\b)", text) if p.strip(" ;；，,。")]
            if len(comma_parts) >= 2:
                return comma_parts
        return [text]

    def _extract_decision_block(text: str, tags: list[str]) -> tuple[dict[str, str], int]:
        normalized = re.sub(r"(?<=\d),(?=\d)", "", text)
        normalized = re.sub(r"\s*(?:->|→|=>)\s*", " -> ", normalized)
        actor_m = ACTOR_RE.search(normalized)
        actor = actor_m.group(1) if actor_m else ""
        arrow_left = ""
        arrow_right = ""
        if " -> " in normalized:
            arrow_left, arrow_right = [p.strip(" ，,。;；") for p in normalized.split(" -> ", 1)]
        condition_candidates = [
            m.group(1).strip(" ，,。;；")
            for m in re.finditer(
                r"(?:\bif\b|\bwhen\b|如果|当|若|仅当)\s+(.+?)(?=(?:\bif\b|\bthen\b|则|可|会|将|can|could|will|,?\s*they\b|$))",
                normalized,
                re.IGNORECASE,
            )
        ]
        if not condition_candidates:
            condition_m = CONDITION_RE.search(normalized)
            condition = condition_m.group(1).strip(" ，,。;；") if condition_m else ""
        else:
            condition = " && ".join(condition_candidates[:2])
        if not condition and arrow_left and ("是否" in arrow_left or "if" in arrow_left.lower() or "when" in arrow_left.lower()):
            condition = re.sub(r"[？?]+$", "", arrow_left).strip()

        action = ""
        if arrow_right:
            action = arrow_right
        action_m = re.search(r"(?:\bthen\b|则)\s*(.+)$", normalized, re.IGNORECASE)
        if action_m and not action:
            action = action_m.group(1).strip(" 。；;")
        if not action:
            action_m = re.search(
                r"(?:,\s*)?(?:(?:they|system|user|用户|系统)\s+)?(?:can|will|shall|可|会|将|进入|获得|receive|get|show|display)\s+(.+)$",
                normalized,
                re.IGNORECASE,
            )
            if action_m:
                action = action_m.group(1).strip(" 。；;")
        if not action:
            action_m = ACTION_RE.search(normalized)
            action = action_m.group(1).strip(" 。；;") if action_m else ""

        status_m = re.search(r"([^\s，,。;；]{1,24}状态)\s*变为\s*[\"“”']?([^\"“”']+)[\"“”']?", normalized)
        if status_m and (not action or len(action) <= 2):
            status_phrase = f"{status_m.group(1)}变为{status_m.group(2).strip()}"
            action = status_phrase

        outcome = ""
        if OUTCOME_RE.search(action):
            outcome = action
        elif OUTCOME_RE.search(normalized):
            outcome = normalized
        elif status_m:
            outcome = action
        elif arrow_right and UNRESOLVED_RE.search(arrow_right):
            outcome = arrow_right
        elif UNRESOLVED_RE.search(normalized):
            outcome = normalized

        thresholds = [m.group(0).strip() for m in NUMERIC_ANCHOR_RE.finditer(normalized)]
        thresholds = list(dict.fromkeys(thresholds))[:6]

        time_hits = [m.group(1).strip() for m in TIME_RE.finditer(normalized)]
        time_window = " | ".join(list(dict.fromkeys(time_hits))[:2]) if time_hits else ""

        exception = normalized if EXCEPTION_RE.search(normalized) else ""
        if not exception and arrow_right and UNRESOLVED_RE.search(arrow_right):
            exception = arrow_right

        confidence = 0
        if actor:
            confidence += 1
        if condition:
            confidence += 2
        if action:
            confidence += 2
        if outcome:
            confidence += 1
        if thresholds:
            confidence += 1
        if time_window:
            confidence += 1
        if tags:
            confidence += 1
        if exception:
            confidence += 1
        block = {
            "actor": actor,
            "condition": condition,
            "action": action,
            "observable_outcome": outcome,
            "thresholds": " | ".join(thresholds[:4]),
            "time_window": time_window,
            "exception": exception,
        }
        return block, confidence

    for line_no, ln in enumerate(lines, start=1):
        t = ln.strip()
        if not t or t.startswith("#"):
            continue
        explicit_tags = _extract_explicit_branch_tags(t)
        inline_tags = explicit_tags
        if _is_scope_marker_line(t, explicit_tags):
            active_scope_id = str(explicit_tags[0])
            active_scope_label = t
            scope_markers.append(
                {
                    "scope_id": active_scope_id,
                    "scope_label": active_scope_label,
                    "branch_ids": explicit_tags,
                    "line_no": line_no,
                }
            )
        if t.startswith("### [") and "http" in t:
            continue
        if (NOISE_LINE_RE.search(t) or _looks_engineering_noise(t)) and not _should_force_semantic_retention(t, inline_tags, 0):
            dropped_noise += 1
            continue
        if not ANCHOR_RE.search(t):
            continue
        score = 0
        if BUSINESS_SIGNAL_RE.search(t):
            score += 3
        if re.search(r"\b(if|when|then)\b|如果|当|则", t, re.IGNORECASE):
            score += 2
        if OUTCOME_RE.search(t):
            score += 1
        if TIME_RE.search(t):
            score += 1
        if ANCHOR_RE.search(t):
            score += 1
        if re.search(r"\d", t):
            score += 1
        if len(t) >= 20:
            score += 1
        if re.search(r"https?://", t):
            score -= 1
        if _looks_engineering_noise(t):
            score -= 3

        pieces = _split_candidate_line(t)
        for piece in pieces:
            piece_tags = _extract_branch_tags(piece) or inline_tags
            piece_score = score
            if piece != t and len(piece) >= 18:
                piece_score += 1
            if piece_score < 3 and not piece_tags:
                dropped_low_signal += 1
                continue
            if piece in seen:
                continue
            seen.add(piece)
            scored_candidates.append(
                {
                    "score": piece_score,
                    "idx": len(scored_candidates),
                    "text": piece,
                    "branch_tags": piece_tags,
                    "semantic_roles": _semantic_roles(piece, {}, piece_tags),
                    "line_no": line_no,
                    "scope_id": active_scope_id,
                    "scope_label": active_scope_label,
                }
            )

    scored_candidates.sort(key=lambda x: (-int(x["score"]), int(x["idx"])))
    selected = scored_candidates[:max_lines]
    semantic_forced: list[dict[str, object]] = []
    for item in scored_candidates[max_lines:]:
        if _should_force_semantic_retention(
            str(item.get("text") or ""),
            list(item.get("branch_tags") or []),
            int(item.get("score") or 0),
        ):
            semantic_forced.append(item)
    selected_texts = {str(x["text"]) for x in selected}
    semantically_forced_kept = 0
    semantic_extra_limit = int(_SEMANTIC_RETENTION.get("max_extra_per_page") or 8)
    for item in semantic_forced[:semantic_extra_limit]:
        text = str(item["text"])
        if text not in selected_texts:
            selected.append(item)
            selected_texts.add(text)
            semantically_forced_kept += 1
    propositions = [str(x["text"]) for x in selected]
    selected_meta = {str(x["text"]): list(x.get("branch_tags") or []) for x in selected}
    selected_scope = {str(x["text"]): (str(x.get("scope_id") or "global"), str(x.get("scope_label") or "global")) for x in selected}
    selected_line_no = {str(x["text"]): int(x.get("line_no") or 0) for x in selected}
    contract_candidates = 0
    evidence_notes = 0
    noise_candidates = 0
    decision_core = 0
    presentation_context = 0
    unresolved_critical = 0
    noise_context = 0
    source_file = str(md_path.relative_to(REPO_ROOT).as_posix())

    for p in propositions:
        phase = _infer_phase(p)
        tags = selected_meta.get(p, [])
        scope_id, scope_label = selected_scope.get(p, ("global", "global"))
        line_no = selected_line_no.get(p, 0)
        block, confidence = _extract_decision_block(p, tags)
        non_empty_fields = sum(1 for v in block.values() if str(v).strip())
        signal = _rule_signal_strength(p)
        track, track_reason, causality_score = _decision_track(p, block, confidence, non_empty_fields, signal)
        semantic_roles = _semantic_roles(p, block, tags)
        ctype, reason, admission = _admit_candidate(
            doc_intent,
            p,
            confidence,
            non_empty_fields,
            signal,
            track,
            causality_score,
        )
        if ctype == "contract_candidate":
            contract_candidates += 1
        elif ctype == "noise_context":
            noise_candidates += 1
        else:
            evidence_notes += 1
        if track == "decision_core":
            decision_core += 1
        elif track == "unresolved_critical":
            unresolved_critical += 1
        elif track == "noise_context":
            noise_context += 1
        else:
            presentation_context += 1
        business_scope_label = _business_scope_label(p, scope_label, tags, semantic_roles)
        proposition_items.append(
            {
                "text": p,
                "doc_intent": doc_intent,
                "candidate_type": ctype,
                "eligibility_reason": reason,
                "decision_track": track,
                "decision_track_reason": track_reason,
                "semantic_roles": semantic_roles,
                "semantic_preservation_reason": _semantic_preservation_reason(semantic_roles, track, ctype),
                "business_scope_label": business_scope_label,
                "causality_score": causality_score,
                "admission_stage1_result": str(admission.get("stage1_result") or ""),
                "admission_stage1_reason": str(admission.get("stage1_reason") or ""),
                "admission_risk_flags": list(admission.get("risk_flags") or []),
                "admission_drop_reason": str(admission.get("drop_reason") or ""),
                "scope_id": scope_id,
                "scope_label": scope_label,
                "semantic_scope_label": business_scope_label,
                "phase": phase,
                "depends_on_phases": _infer_dependencies(p, phase),
                "branch_ids": tags,
                "branch_name": " / ".join(tags) if tags else "",
                "branch_condition": p if tags else "",
                "branch_outcome": "",
                "evidence_span": {
                    "source_file": source_file,
                    "start_line": line_no,
                    "end_line": line_no,
                },
                "decision_block": block,
                "decision_confidence": confidence,
                "decision_fields_count": non_empty_fields,
                "decision_missing_fields": [k for k, v in block.items() if not str(v).strip()],
            }
        )

    return {
        "materialized_file": str(md_path.relative_to(REPO_ROOT).as_posix()),
        "source_system": _source_system(md_path),
        "title": title,
        "source_url": source_url,
        "doc_intent": doc_intent,
        "doc_intent_confidence": doc_intent_confidence,
        "propositions": propositions,
        "proposition_items": proposition_items,
        "structured_source": structured_signal,
        "scope_markers": scope_markers,
        "candidate_meta": {
            "selected": len(propositions),
            "contract_candidates": contract_candidates,
            "evidence_notes": evidence_notes,
            "noise_candidates": noise_candidates,
            "decision_core": decision_core,
            "presentation_context": presentation_context,
            "unresolved_critical": unresolved_critical,
            "noise_context": noise_context,
            "semantically_forced_kept": semantically_forced_kept,
            "dropped_noise": dropped_noise,
            "dropped_low_signal": dropped_low_signal,
        },
    }


def _write_outputs(curated_root: Path, root_id: str, slug: str, pages: list[dict[str, object]]) -> None:
    agg_dir = curated_root / "_aggregate" / slug
    agg_dir.mkdir(parents=True, exist_ok=True)
    json_path = agg_dir / f"{slug}-propositions.json"
    md_path = agg_dir / f"{slug}-命题清单.md"

    payload = {
        "root_id": root_id,
        "slug": slug,
        "pages_total": len(pages),
        "pages_with_props": sum(1 for p in pages if p.get("propositions")),
        "pages": pages,
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    out = [
        f"# {slug} · 命题清单（S3.5）",
        "",
        "## 说明",
        "- 本文件是逐页命题候选，不是最终定稿。",
        "- 每页候选命题用于 S4/S5 的规则链重组与核对。",
        "",
        "## 命题候选（按来源页）",
    ]
    for i, page in enumerate(pages, start=1):
        title = str(page.get("title") or "")
        url = str(page.get("source_url") or "")
        materialized_file = str(page.get("materialized_file") or "")
        source_system = str(page.get("source_system") or "confluence")
        doc_intent = str(page.get("doc_intent") or "rule_spec")
        props = list(page.get("propositions") or [])
        items = list(page.get("proposition_items") or [])
        markers = list(page.get("scope_markers") or [])
        structured = dict(page.get("structured_source") or {})
        out.append(f"### {i}. {title}")
        out.append(f"- 来源系统：`{source_system}`")
        out.append(f"- 来源页：{url or '(missing source url)'}")
        out.append(f"- 物化文件：`{materialized_file}`")
        out.append(f"- 文档意图：`{doc_intent}`")
        if structured.get("has_structured_source"):
            terms = ", ".join(str(x) for x in list(structured.get("header_terms") or [])[:8])
            samples = "；".join(str(x) for x in list(structured.get("sample_lines") or [])[:3])
            out.append(
                "- 结构化来源信号："
                f"表头/字段={terms or '-'}；"
                f"value_lines={structured.get('value_line_count', 0)}；"
                f"mapping_lines={structured.get('mapping_line_count', 0)}"
            )
            if samples:
                out.append(f"  - 样例：{samples}")
        if markers:
            out.append("- 作用域标记：")
            for marker in markers:
                m = dict(marker)
                out.append(
                    f"  - `{m.get('scope_id')}` @L{m.get('line_no')}: {m.get('scope_label')}"
                )
        if not props:
            out.append("- 命题候选：_（未抽取到明显命题，请人工补录）_")
        else:
            out.append("- Contract 候选（进入决策链，按作用域）：")
            grouped: dict[str, list[dict[str, object]]] = {}
            order: list[str] = []
            contract_items = [dict(it) for it in items if str(it.get("candidate_type") or "") == "contract_candidate"]
            evidence_items = [
                dict(it)
                for it in items
                if str(it.get("candidate_type") or "") == "evidence_note"
            ]
            noise_items = [
                dict(it)
                for it in items
                if str(it.get("candidate_type") or "") == "noise_context"
            ]
            for it in contract_items:
                scope = str(it.get("scope_id") or "global")
                if scope not in grouped:
                    grouped[scope] = []
                    order.append(scope)
                grouped[scope].append(dict(it))
            if not grouped:
                out.append("  - （无）")
            else:
                for scope in order:
                    chunk = grouped.get(scope) or []
                    label = str(chunk[0].get("scope_label") or scope)
                    out.append(f"  - [{scope}] {label}")
                    for it in chunk:
                        span = dict(it.get("evidence_span") or {})
                        start_line = int(span.get("start_line") or 0)
                        line_hint = f" @L{start_line}" if start_line > 0 else ""
                        out.append(f"    -{line_hint} {it.get('text')}")
            if evidence_items:
                out.append("- Evidence 备注（延迟裁决，供 S4 语义重挂载核对）：")
                for it in evidence_items:
                    span = dict(it.get("evidence_span") or {})
                    start_line = int(span.get("start_line") or 0)
                    line_hint = f" @L{start_line}" if start_line > 0 else ""
                    reason = str(it.get("eligibility_reason") or "")
                    roles = ", ".join(str(x) for x in list(it.get("semantic_roles") or []))
                    out.append(f"  -{line_hint} {it.get('text')} 〔{reason}; roles={roles or 'none'}〕")
            if noise_items:
                out.append("- Noise 隔离（默认不进入 S4 决策重挂载）：")
                for it in noise_items:
                    span = dict(it.get("evidence_span") or {})
                    start_line = int(span.get("start_line") or 0)
                    line_hint = f" @L{start_line}" if start_line > 0 else ""
                    reason = str(it.get("admission_drop_reason") or it.get("eligibility_reason") or "")
                    out.append(f"  -{line_hint} {it.get('text')} 〔{reason}〕")
        out.append("")
    md_path.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")


def _load_closure(curated_root: Path) -> dict[str, str]:
    path = curated_root / "_materialization_closure.json"
    if not path.is_file():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, json.JSONDecodeError):
        return {}
    return {
        str(src).strip(): str(target).strip()
        for src, target in raw.items()
        if str(src).strip() and str(target).strip()
    }


def _resolve_closure_source_path(curated_root: Path, rules_root: Path, rel: str) -> Path:
    if rel.startswith("jira/materialized/"):
        return curated_root / rel
    return rules_root / rel


def _source_pages_for_slug(curated_root: Path, rules_root: Path, closure: dict[str, str], slug: str) -> list[Path]:
    prefix = f"_deliver/{slug}/"
    pages: list[Path] = []
    for rel, target in sorted(closure.items()):
        if not target.startswith(prefix):
            continue
        path = _resolve_closure_source_path(curated_root, rules_root, rel)
        if path.is_file():
            pages.append(path)
    return pages


def _load_s2_decisions(curated_root: Path) -> list[dict[str, object]]:
    path = curated_root / "S2_DECISION_LEDGER.json"
    if not path.is_file():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, json.JSONDecodeError):
        return []
    return [dict(x) for x in list(payload.get("decisions") or []) if isinstance(x, dict)]


def _write_cross_slug_handoff(curated_root: Path, closure: dict[str, str], decisions: list[dict[str, object]]) -> None:
    entries: list[dict[str, object]] = []
    for row in decisions:
        rel = str(row.get("materialized_file") or "").strip()
        reason = str(row.get("reason") or "").strip()
        target = closure.get(rel, "")
        if "cross-slug" not in reason or not target.startswith("_deliver/"):
            continue
        parts = target.split("/")
        target_slug = parts[1] if len(parts) > 1 else ""
        if not target_slug:
            continue
        entries.append(
            {
                "materialized_file": rel,
                "source_facet": str(row.get("source_facet") or "").strip(),
                "target_slug": target_slug,
                "confidence": str(row.get("confidence") or "").strip(),
                "score": row.get("score"),
                "reason": reason,
                "target": target,
            }
        )

    agg_root = curated_root / "_aggregate"
    agg_root.mkdir(parents=True, exist_ok=True)
    (agg_root / "CROSS_SLUG_HANDOFF.json").write_text(
        json.dumps(
            {
                "root_id": curated_root.name,
                "cross_slug_total": len(entries),
                "entries": entries,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Cross-slug handoff（S3）",
        "",
        "## 说明",
        "- 本文件记录 S2 在 primary facet 内发现的页面级跨主题转交。",
        "- 它是 S3 给 S5 的审计线索；Agent 仍需按 S5 领域模型决定吸收、降层或排除。",
        "",
        "## 转交列表",
    ]
    if not entries:
        lines.append("- 无")
    else:
        for item in entries:
            lines.append(
                "- "
                f"`{item['materialized_file']}` -> `{item['target_slug']}` "
                f"（confidence={item['confidence'] or '-'} / score={item['score']} / {item['reason']}）"
            )
    (agg_root / "CROSS_SLUG_HANDOFF.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    args = _parse_args()
    root_id = str(args.root_id).strip()
    curated_root = CURATED_BY_ROOT / root_id
    rules_root = MATERIALIZED_BY_ROOT / root_id
    checklist = resolve_checklist_file(curated_root)
    if checklist is None:
        print(f"Missing checklist: {curated_root / 'DOMAIN_MODULE_CHECKLIST.md'}", file=sys.stderr)
        return 1
    if not rules_root.is_dir():
        print(f"Missing materialized root: {rules_root}", file=sys.stderr)
        return 1

    checklist_text = checklist.read_text(encoding="utf-8", errors="replace")
    if _has_pending_status(checklist_text) and not args.allow_unconfirmed:
        print(
            "S2 confirm gate is still open: DOMAIN_MODULE_CHECKLIST.md contains '待确认'. "
            "Mark checklist rows as '确认' before running Compose (S3+), "
            "or pass --allow-unconfirmed to override explicitly.",
            file=sys.stderr,
        )
        return 2
    confirmed = _confirmed_slugs(checklist_text)
    only = {s.strip() for s in args.only_slug if s.strip()}
    if only:
        confirmed = [(slug, cn) for slug, cn in confirmed if slug in only]
    if not confirmed:
        print("No confirmed theme slug selected; nothing to do.")
        return 0

    closure = _load_closure(curated_root)
    s2_decisions = _load_s2_decisions(curated_root)
    _write_cross_slug_handoff(curated_root, closure, s2_decisions)
    done: list[str] = []
    for slug, _theme_cn in confirmed:
        pages: list[dict[str, object]] = []
        for md in _source_pages_for_slug(curated_root, rules_root, closure, slug):
            pages.append(_parse_page(md, args.max_lines_per_page))
        _write_outputs(curated_root, root_id, slug, pages)
        done.append(slug)
    print(f"Proposition extraction complete for root_id={root_id}: {', '.join(done)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
