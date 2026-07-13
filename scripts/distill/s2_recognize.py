#!/usr/bin/env python3
"""S2 Recognize: build decision ledger, review decisions, checklist, closure."""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

_SCRIPTS = next(p for p in Path(__file__).resolve().parents if (p / "_install.py").is_file())
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
import _install

_install.bootstrap(__file__)

from runtime.checklist_modules import (
    render_checklist_header,
    render_module_block,
    statuses_by_slug,
)
from runtime.domain_knowledge_paths import CURATED_BY_ROOT, MATERIALIZED_BY_ROOT
from runtime.domain_profiles import load_s2_profiles, require_checklist_themes
from jira.lib.attribution_yaml import parse_attribution_yaml_file
from teams.registry import jira_theme_to_proposition_slug, team_key_for_root_id

SLUGS: list[tuple[str, str, str]] = []
S2_PROFILES: dict = {}
VALID_SLUGS: set[str] = set()
APPENDIX_TARGET = "_附录/非业务/非业务资料索引.md"
FACET_TO_SLUG: dict[str, str] = {}
DOMAIN_CUES: dict[str, re.Pattern[str]] = {}
BUSINESS_SIGNAL_RE: re.Pattern[str]
STRONG_CUE_RE: re.Pattern[str]
ENGINEERING_NOISE_RE: re.Pattern[str]
HARD_NON_BUSINESS_RE: re.Pattern[str]
EXPLICIT_NON_BUSINESS_RE: re.Pattern[str]
ROUTE_OVERRIDE_RULES: list[tuple[re.Pattern[str], str, str]] = []
API_RE = re.compile(r"(/[\w\-{}$]+){2,}|https?://", re.IGNORECASE)
NO_TEXT_MARKER_RE = re.compile(r"无可用纯文本|白板|图表|宏")


def _configure_profiles(scope: str) -> None:
    global SLUGS
    global S2_PROFILES
    global VALID_SLUGS
    global FACET_TO_SLUG
    global DOMAIN_CUES
    global BUSINESS_SIGNAL_RE
    global STRONG_CUE_RE
    global ENGINEERING_NOISE_RE
    global HARD_NON_BUSINESS_RE
    global EXPLICIT_NON_BUSINESS_RE
    global ROUTE_OVERRIDE_RULES

    SLUGS = require_checklist_themes(scope)
    S2_PROFILES = load_s2_profiles(scope)
    VALID_SLUGS = set(S2_PROFILES["domain_cues"].keys()) | {x[0] for x in SLUGS}
    FACET_TO_SLUG = S2_PROFILES["primary_facet_to_slug"]
    DOMAIN_CUES = S2_PROFILES["domain_cues"]
    BUSINESS_SIGNAL_RE = S2_PROFILES["business_signal_re"]
    STRONG_CUE_RE = S2_PROFILES["strong_cue_re"]
    ENGINEERING_NOISE_RE = S2_PROFILES["engineering_noise_re"]
    HARD_NON_BUSINESS_RE = S2_PROFILES["hard_non_business_path_re"]
    EXPLICIT_NON_BUSINESS_RE = S2_PROFILES["explicit_non_business_path_re"]
    ROUTE_OVERRIDE_RULES = S2_PROFILES["route_overrides"]


@dataclass
class DecisionEntry:
    materialized_file: str
    source_facet: str
    decision_mode: str  # primary|rescued|appendix
    proposed_slug: str | None
    confidence: str
    score: int
    reason: str
    evidence_tokens: list[str]
    is_no_text: bool


@dataclass(frozen=True)
class SourceRecord:
    source_system: str  # confluence|jira
    source_id: str
    materialized_file: str
    source_facet: str
    body_path: Path | None
    attribution: dict[str, object]


@dataclass
class ReviewDecision:
    materialized_file: str
    action: str  # pending|keep|reassign|appendix
    resolved_slug: str | None
    note: str


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="S2 Recognize with decision ledger.")
    p.add_argument("--root-id", required=True, help="Confluence root page ID")
    p.add_argument(
        "--rescue-threshold",
        type=int,
        default=2,
        help="Minimum score to propose rescue into a business slug",
    )
    return p.parse_args()


def _target_work_draft(slug: str) -> str:
    from runtime.deliverable_locale import default_locale, token

    suffix = token("filenames.work_draft_suffix", default_locale())
    return f"_deliver/{slug}/{slug}{suffix}"


def _pending_status() -> str:
    from runtime.deliverable_locale import default_locale, token

    return token("checklist.status_pending", default_locale())


def _not_archived_status() -> str:
    from runtime.deliverable_locale import default_locale, token

    return token("checklist.status_not_archived", default_locale())


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))


def _title_path_text(rel_path: str, body: str) -> str:
    title_lines: list[str] = [rel_path]
    for line in body.splitlines()[:20]:
        stripped = line.strip()
        if stripped.startswith("#"):
            title_lines.append(stripped)
    return "\n".join(title_lines)


def _primary_cross_slug_override(
    rel_path: str,
    body: str,
    fixed_slug: str,
) -> DecisionEntry | None:
    """Allow page-level title/path overrides inside a primary facet.

    Primary facet routing is still useful as a default, but it must not suppress
    clear page-title evidence that a page belongs to another confirmed domain.
    Restrict this check to path/title text so incidental body mentions, such as
    checkout pages mentioning shipping address, do not cause noisy reassignment.
    """

    title_path = _title_path_text(rel_path, body)
    for pat, forced_slug, reason in ROUTE_OVERRIDE_RULES:
        if forced_slug == fixed_slug or forced_slug not in VALID_SLUGS:
            continue
        if not pat.search(title_path):
            continue
        return DecisionEntry(
            materialized_file=rel_path,
            source_facet=rel_path.split("/", 1)[0],
            decision_mode="rescued",
            proposed_slug=forced_slug,
            confidence="high",
            score=101,
            reason=f"primary facet cross-slug override ({fixed_slug} -> {forced_slug}): {reason}",
            evidence_tokens=_extract_evidence(title_path),
            is_no_text=bool(NO_TEXT_MARKER_RE.search(body)),
        )
    return None


def _existing_statuses(checklist_path: Path) -> dict[str, str]:
    if not checklist_path.is_file():
        return {}
    return statuses_by_slug(_read(checklist_path))


def _extract_evidence(raw: str, max_items: int = 6) -> list[str]:
    tokens: list[str] = []
    for slug, cue in DOMAIN_CUES.items():
        for m in cue.findall(raw):
            val = str(m).strip()
            if not val:
                continue
            if val not in tokens:
                tokens.append(val)
            if len(tokens) >= max_items:
                return tokens
    return tokens


def _secondary_recall(rel_path: str, body: str, rescue_threshold: int) -> DecisionEntry:
    raw = f"{rel_path}\n{body}"
    if EXPLICIT_NON_BUSINESS_RE.search(rel_path):
        return DecisionEntry(
            materialized_file=rel_path,
            source_facet=rel_path.split("/", 1)[0],
            decision_mode="appendix",
            proposed_slug=None,
            confidence="high",
            score=0,
            reason="explicit hard non-business path",
            evidence_tokens=[],
            is_no_text=False,
        )
    is_no_text = bool(NO_TEXT_MARKER_RE.search(body))
    strong_hit = bool(STRONG_CUE_RE.search(raw))
    business_hit = bool(BUSINESS_SIGNAL_RE.search(raw))
    api_hit = bool(API_RE.search(raw))
    hard_non_business = bool(HARD_NON_BUSINESS_RE.search(rel_path))

    best_score = 0
    best_slug = ""
    second_score = 0
    scores: list[tuple[int, str]] = []
    for slug, cue in DOMAIN_CUES.items():
        cue_hits = len(cue.findall(raw))
        score = cue_hits
        if cue_hits > 0 and business_hit:
            score += 1
        if cue_hits > 0 and api_hit:
            score += 1
        scores.append((score, slug))
    scores.sort(reverse=True)
    if scores:
        best_score, best_slug = scores[0]
    if len(scores) > 1:
        second_score = scores[1][0]

    override_slug = ""
    override_reason = ""
    for pat, forced_slug, reason in ROUTE_OVERRIDE_RULES:
        if pat.search(raw):
            override_slug = forced_slug
            override_reason = reason
            break
    if override_slug:
        best_slug = override_slug

    if best_score <= 0 or (hard_non_business and not override_slug):
        return DecisionEntry(
            materialized_file=rel_path,
            source_facet=rel_path.split("/", 1)[0],
            decision_mode="appendix",
            proposed_slug=None,
            confidence="high",
            score=max(best_score, 0),
            reason="no domain cues",
            evidence_tokens=_extract_evidence(raw),
            is_no_text=is_no_text,
        )
    if ENGINEERING_NOISE_RE.search(raw) and not business_hit and not api_hit:
        return DecisionEntry(
            materialized_file=rel_path,
            source_facet=rel_path.split("/", 1)[0],
            decision_mode="appendix",
            proposed_slug=None,
            confidence="high",
            score=best_score,
            reason="engineering noise page without business/API signals",
            evidence_tokens=_extract_evidence(raw),
            is_no_text=is_no_text,
        )

    reason = "domain cues from title/body"
    confidence = "medium"
    if strong_hit and best_score >= 3 and best_score - second_score >= 1:
        confidence = "high"
        reason = "business signals + domain cues"
    if is_no_text and strong_hit and best_score >= 1:
        confidence = "low"
        reason = "no-text page with business title cues"
    if override_reason:
        reason = f"{reason} + {override_reason}"

    rescue_ok = (best_score >= rescue_threshold) or (is_no_text and strong_hit and best_score >= 1)
    if rescue_ok and best_slug in VALID_SLUGS:
        return DecisionEntry(
            materialized_file=rel_path,
            source_facet=rel_path.split("/", 1)[0],
            decision_mode="rescued",
            proposed_slug=best_slug,
            confidence=confidence,
            score=best_score,
            reason=reason,
            evidence_tokens=_extract_evidence(raw),
            is_no_text=is_no_text,
        )

    return DecisionEntry(
        materialized_file=rel_path,
        source_facet=rel_path.split("/", 1)[0],
        decision_mode="appendix",
        proposed_slug=None,
        confidence=confidence,
        score=best_score,
        reason="below rescue threshold",
        evidence_tokens=_extract_evidence(raw),
        is_no_text=is_no_text,
    )


def _load_confluence_manifest_targets(mat_root: Path) -> list[str]:
    manifest = mat_root / "_materialized_manifest.json"
    if not manifest.is_file():
        return []
    try:
        payload = json.loads(manifest.read_text(encoding="utf-8", errors="replace"))
    except (OSError, json.JSONDecodeError):
        return []
    targets: list[str] = []
    for row in list(payload.get("targets") or []):
        rel = str((row or {}).get("path") or "").strip()
        if rel and rel.endswith(".md"):
            targets.append(rel)
    return sorted(dict.fromkeys(targets))


def _confluence_sources(mat_root: Path) -> list[SourceRecord]:
    rels = _load_confluence_manifest_targets(mat_root)
    if not rels:
        rels = [
            path.relative_to(mat_root).as_posix()
            for path in sorted(mat_root.rglob("*.md"))
            if path.name != "README.md"
        ]
    out: list[SourceRecord] = []
    for rel in rels:
        path = mat_root / rel
        if not path.is_file():
            continue
        source_facet = rel.split("/", 1)[0] if "/" in rel else "materialized"
        out.append(
            SourceRecord(
                source_system="confluence",
                source_id=rel,
                materialized_file=rel,
                source_facet=source_facet,
                body_path=path,
                attribution={},
            )
        )
    return out


def _as_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    text = str(value).strip()
    return [text] if text else []


def _jira_sources(curated_root: Path) -> list[SourceRecord]:
    jira_root = curated_root / "jira"
    attr_dir = jira_root / "attribution"
    mat_dir = jira_root / "materialized"
    if not attr_dir.is_dir():
        return []
    out: list[SourceRecord] = []
    for attr_path in sorted(attr_dir.glob("*.yaml")):
        try:
            meta = parse_attribution_yaml_file(attr_path)
        except OSError:
            continue
        key = str(meta.get("key") or attr_path.stem).strip() or attr_path.stem
        rel = f"jira/materialized/{key}.md"
        mat_path = mat_dir / f"{key}.md"
        primary = str(meta.get("primary") or "").strip()
        source_facet = f"jira:{primary or 'unassigned'}"
        out.append(
            SourceRecord(
                source_system="jira",
                source_id=key,
                materialized_file=rel,
                source_facet=source_facet,
                body_path=mat_path if mat_path.is_file() else None,
                attribution={"key": key, **meta},
            )
        )
    return out


def _source_registry(mat_root: Path, curated_root: Path) -> list[SourceRecord]:
    sources = _confluence_sources(mat_root)
    sources.extend(_jira_sources(curated_root))
    return sources


def _jira_decision(source: SourceRecord, root_id: str) -> DecisionEntry:
    meta = source.attribution
    team_key = team_key_for_root_id(root_id) or ""

    def _map_theme(slug: str) -> str:
        return jira_theme_to_proposition_slug(team_key, slug) if team_key else slug

    primary = _map_theme(str(meta.get("primary") or "").strip())
    themes = [x for x in (_map_theme(t) for t in _as_list(meta.get("themes"))) if x in VALID_SLUGS]
    target_slug = primary if primary in VALID_SLUGS else (themes[0] if themes else "")
    tier = str(meta.get("distill_tier") or "").strip()
    admitted = tier in {"proposition_core", "platform_variant"} or bool(
        meta.get("proposition_extract") or meta.get("business_extract")
    )
    if target_slug and admitted:
        return DecisionEntry(
            materialized_file=source.materialized_file,
            source_facet=source.source_facet,
            decision_mode="primary",
            proposed_slug=target_slug,
            confidence=str(meta.get("confidence") or "medium"),
            score=100 if tier == "proposition_core" else 80,
            reason=f"jira attribution route ({tier or 'legacy-business-extract'})",
            evidence_tokens=[x for x in [source.source_id, target_slug, tier] if x],
            is_no_text=source.body_path is None,
        )
    return DecisionEntry(
        materialized_file=source.materialized_file,
        source_facet=source.source_facet,
        decision_mode="appendix",
        proposed_slug=None,
        confidence=str(meta.get("confidence") or "medium"),
        score=0,
        reason=f"jira attribution not admitted to business compose ({tier or 'no-distill-tier'})",
        evidence_tokens=[x for x in [source.source_id, primary, tier] if x],
        is_no_text=source.body_path is None,
    )


def _confluence_decision(source: SourceRecord, rescue_threshold: int) -> DecisionEntry:
    rel = source.materialized_file
    body = _read(source.body_path) if source.body_path else ""
    fixed_slug = FACET_TO_SLUG.get(source.source_facet)
    if fixed_slug:
        cross_slug = _primary_cross_slug_override(rel, body, fixed_slug)
        if cross_slug is not None:
            return cross_slug
        return DecisionEntry(
            materialized_file=rel,
            source_facet=source.source_facet,
            decision_mode="primary",
            proposed_slug=fixed_slug,
            confidence="high",
            score=100,
            reason=f"primary facet route ({source.source_facet})",
            evidence_tokens=[source.source_facet],
            is_no_text=False,
        )
    return _secondary_recall(rel, body, rescue_threshold)


def _build_machine_decisions(mat_root: Path, rescue_threshold: int, curated_root: Path | None = None) -> list[DecisionEntry]:
    curated = curated_root or Path()
    root_id = curated.name if curated_root else ""
    rows: list[DecisionEntry] = []
    for source in _source_registry(mat_root, curated):
        if source.source_system == "jira":
            rows.append(_jira_decision(source, root_id))
        else:
            rows.append(_confluence_decision(source, rescue_threshold))
    return rows


def _load_review_map(path: Path) -> dict[str, ReviewDecision]:
    if not path.is_file():
        return {}
    try:
        payload = _read_json(path)
    except (json.JSONDecodeError, OSError):
        return {}
    out: dict[str, ReviewDecision] = {}
    for row in payload.get("decisions") or []:
        materialized = str(row.get("materialized_file") or "").strip()
        action = str(row.get("action") or "").strip() or "pending"
        resolved_slug = str(row.get("resolved_slug") or "").strip() or None
        note = str(row.get("note") or "").strip()
        if materialized:
            out[materialized] = ReviewDecision(
                materialized_file=materialized,
                action=action,
                resolved_slug=resolved_slug,
                note=note,
            )
    return out


def _initial_review_action(entry: DecisionEntry) -> str:
    if entry.decision_mode in {"primary", "rescued"}:
        return "keep"
    return "appendix"


def _build_review_decisions(machine_rows: list[DecisionEntry], old_map: dict[str, ReviewDecision]) -> list[ReviewDecision]:
    out: list[ReviewDecision] = []
    for row in machine_rows:
        # Require human review only for rescued pages.
        if row.decision_mode != "rescued":
            continue
        prev = old_map.get(row.materialized_file)
        if prev and prev.action in {"pending", "keep", "reassign", "appendix"}:
            resolved = prev.resolved_slug if prev.resolved_slug else None
            normalized_action = prev.action
            if normalized_action == "pending":
                normalized_action = "keep"
            out.append(
                ReviewDecision(
                    materialized_file=row.materialized_file,
                    action=normalized_action,
                    resolved_slug=resolved,
                    note=prev.note,
                )
            )
            continue
        out.append(
            ReviewDecision(
                materialized_file=row.materialized_file,
                action=_initial_review_action(row),
                resolved_slug=None,
                note="",
            )
        )
    return out


def _review_map(decisions: list[ReviewDecision]) -> dict[str, ReviewDecision]:
    return {d.materialized_file: d for d in decisions}


def _resolve_target(machine: DecisionEntry, review: ReviewDecision | None) -> str:
    if review is None:
        if machine.decision_mode in {"primary", "rescued"} and machine.proposed_slug:
            return _target_work_draft(machine.proposed_slug)
        return APPENDIX_TARGET

    if review.action == "appendix":
        return APPENDIX_TARGET
    if review.action == "reassign" and review.resolved_slug:
        return _target_work_draft(review.resolved_slug)
    if review.action in {"pending", "keep"} and machine.proposed_slug:
        return _target_work_draft(machine.proposed_slug)
    return APPENDIX_TARGET


def _build_checklist(
    curated_root: Path,
    statuses: dict[str, str],
    machine_rows: list[DecisionEntry],
    review_rows: list[ReviewDecision],
) -> None:
    review_map = _review_map(review_rows)
    scan_dirs_by_slug: dict[str, set[str]] = {}
    for row in machine_rows:
        target = _resolve_target(row, review_map.get(row.materialized_file))
        if target.startswith("_deliver/"):
            parts = target.split("/")
            if len(parts) >= 2:
                scan_dirs_by_slug.setdefault(parts[1], set()).add(row.source_facet)

    lines = render_checklist_header(curated_root.name)
    base_slugs = {slug for slug, _, _ in SLUGS}
    extra_slugs: set[str] = set()
    for row in machine_rows:
        if row.proposed_slug and row.proposed_slug not in base_slugs:
            extra_slugs.add(row.proposed_slug)
    for row in review_rows:
        if row.resolved_slug and row.resolved_slug not in base_slugs:
            extra_slugs.add(row.resolved_slug)

    for slug, cn, axis in SLUGS:
        status = statuses.get(slug, _pending_status())
        scan_dirs = _render_scan_dirs(scan_dirs_by_slug.get(slug), slug)
        lines.extend(
            render_module_block(
                theme=cn,
                slug=slug,
                axis=axis,
                scan_dirs=scan_dirs,
                main_entry=_target_work_draft(slug),
                status=status,
                note="S2 decision ledger (awaiting human confirm)",
            )
        )
    for slug in sorted(extra_slugs):
        status = statuses.get(slug, _pending_status())
        scan_dirs = _render_scan_dirs(scan_dirs_by_slug.get(slug), slug)
        lines.extend(
            render_module_block(
                theme=f"New business module ({slug})",
                slug=slug,
                axis="To fill (S2-discovered module)",
                scan_dirs=scan_dirs,
                main_entry=_target_work_draft(slug),
                status=status,
                note="Source: S2_REVIEW_DECISIONS",
            )
        )
    lines.extend(
        render_module_block(
            theme="Non-business / engineering material",
            slug=None,
            axis="Non-domain or deferred",
            scan_dirs="`facet-gateway/`, `facet-misc/`, `facet-unmatched/`",
            main_entry=APPENDIX_TARGET,
            status=_not_archived_status(),
            note="Not on Compose mainline",
        )
    )
    (curated_root / "DOMAIN_MODULE_CHECKLIST.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _render_scan_dirs(scan_dirs: set[str] | None, fallback_slug: str) -> str:
    dirs = sorted(x for x in (scan_dirs or set()) if x)
    if not dirs:
        dirs = [f"facet-{fallback_slug}"]
    return "、".join(f"`{x}/`" for x in dirs)


def _write_non_business_index(curated_root: Path, non_business: list[str], review_decisions: list[ReviewDecision]) -> None:
    out = [
        "# 非业务资料索引",
        "",
        "## 文档用途",
        "- 下列页面判定为非业务/工程资料，不进入 S3-S6 主线。",
        "",
        "## 页面清单",
    ]
    for p in non_business:
        out.append(f"- `{p}`")
    out += ["", "## 疑似业务候选（待人工确认）"]
    if not review_decisions:
        out.append("- 无")
    else:
        for d in review_decisions:
            out.append(f"- `{d.materialized_file}`（action={d.action}, resolved_slug={d.resolved_slug or '-'}）")
    p = curated_root / "_附录/非业务/非业务资料索引.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")


def _write_recall_review(curated_root: Path, machine_rows: list[DecisionEntry], review_map: dict[str, ReviewDecision], threshold: int) -> None:
    rescued = [x for x in machine_rows if x.decision_mode == "rescued"]
    rescued.sort(key=lambda x: (-x.score, x.materialized_file))
    out = [
        "# S2 疑似漏识别清单",
        "",
        "## 判定规则",
        f"- 二次召回阈值：`score >= {threshold}`（`no-text` 页面允许低置信候选）。",
        "- 该清单用于提示二次召回页面；人工确认入口仍以 DOMAIN_MODULE_CHECKLIST.md 为准。",
        "",
        "## 候选列表",
    ]
    if not rescued:
        out.append("- 无")
    else:
        for i, x in enumerate(rescued, start=1):
            rv = review_map.get(x.materialized_file)
            action = rv.action if rv else "pending"
            resolved = rv.resolved_slug if rv and rv.resolved_slug else "-"
            out.append(
                f"- {i}. `{x.materialized_file}` -> `{x.proposed_slug}`（score={x.score} / confidence={x.confidence} / action={action} / resolved_slug={resolved} / {x.reason}）"
            )
    (curated_root / "S2_RECALL_REVIEW.md").write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")


def _write_ledgers(curated_root: Path, root_id: str, machine_rows: list[DecisionEntry], review_rows: list[ReviewDecision]) -> None:
    machine_payload = {
        "root_id": root_id,
        "decisions_total": len(machine_rows),
        "rescued_total": sum(1 for x in machine_rows if x.decision_mode == "rescued"),
        "appendix_total": sum(1 for x in machine_rows if x.decision_mode == "appendix"),
        "primary_total": sum(1 for x in machine_rows if x.decision_mode == "primary"),
        "decisions": [asdict(x) for x in machine_rows],
    }
    review_payload = {
        "root_id": root_id,
        "review_required_total": len(review_rows),
        "pending_total": sum(1 for x in review_rows if x.action == "pending"),
        "decisions": [asdict(x) for x in review_rows],
    }
    (curated_root / "S2_DECISION_LEDGER.json").write_text(
        json.dumps(machine_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (curated_root / "S2_REVIEW_DECISIONS.json").write_text(
        json.dumps(review_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    args = _parse_args()
    root_id = str(args.root_id).strip()
    _configure_profiles(root_id)
    mat_root = MATERIALIZED_BY_ROOT / root_id
    curated_root = CURATED_BY_ROOT / root_id
    if not mat_root.is_dir():
        print(f"Missing materialized root: {mat_root}", file=sys.stderr)
        return 1
    curated_root.mkdir(parents=True, exist_ok=True)

    old_statuses = _existing_statuses(curated_root / "DOMAIN_MODULE_CHECKLIST.md")
    machine_rows = _build_machine_decisions(mat_root, args.rescue_threshold, curated_root)

    old_review_map = _load_review_map(curated_root / "S2_REVIEW_DECISIONS.json")
    review_rows = _build_review_decisions(machine_rows, old_review_map)
    review_map = _review_map(review_rows)

    closure: dict[str, str] = {}
    non_business: list[str] = []
    for row in machine_rows:
        target = _resolve_target(row, review_map.get(row.materialized_file))
        closure[row.materialized_file] = target
        if target == APPENDIX_TARGET:
            non_business.append(row.materialized_file)

    (curated_root / "_materialization_closure.json").write_text(
        json.dumps(closure, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    _write_ledgers(curated_root, root_id, machine_rows, review_rows)
    _build_checklist(curated_root, old_statuses, machine_rows, review_rows)
    _write_non_business_index(curated_root, non_business, review_rows)
    _write_recall_review(curated_root, machine_rows, review_map, args.rescue_threshold)

    pending = sum(1 for x in review_rows if x.action == "pending")
    rescued = sum(1 for x in machine_rows if x.decision_mode == "rescued")
    print(
        f"S2 recognize complete: root_id={root_id} decisions={len(machine_rows)} "
        f"rescued={rescued} review_pending={pending} non_business={len(non_business)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

