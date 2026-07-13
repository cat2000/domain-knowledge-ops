"""Pure logic for S6 reader-facing final draft quality checks."""
from __future__ import annotations

from dataclasses import dataclass
import json
import re
from pathlib import Path

from distill._paths import DISTILLED_BY_ROOT, PASS_MARKER, REPO_ROOT

DEFAULT_READER_LANGUAGE_POLICY = REPO_ROOT / "domain-knowledge" / "language" / "s6-reader-language-policy.json"

REQUIRED_SECTIONS = (
    "## 概述与范围",
    "## 不在本文展开",
    "## 领域模型摘要",
    "## 核心业务规则",
    "## 术语说明",
    "## 待确认事项",
    "## 溯源",
)
GAP_CATEGORIES = ("领域边界", "规则冲突", "数据与接口", "政策与展示", "待补充材料")
MODEL_SUMMARY_LABELS = ("一等业务对象", "对象关系", "状态机/状态转换")
DECISION_CARD_LABELS = ("已确认规则", "待确认边界", "用户可见影响", "关联待确认事项")
GAP_ITEM_LABELS = ("影响规则", "待确认/待补充", "建议确认人", "确认后影响")
KEY_DETAILS_HEADING = "## 关键明细"
S5_STRUCTURED_DETAIL_HEADING = "## 结构化明细转交"

# Token keys for multi-locale validators.
_S6_REQUIRED_SECTION_KEYS = (
    "s6_s7_headings.overview_scope",
    "s6_s7_headings.out_of_scope",
    "s6_s7_headings.domain_model_summary",
    "s6_s7_headings.core_business_rules",
    "s6_s7_headings.glossary",
    "s6_s7_headings.open_items",
    "s6_s7_headings.provenance",
)
_DECISION_CARD_LABEL_KEYS = (
    "s7_decision_card_labels.confirmed_rule",
    "s7_decision_card_labels.open_boundary",
    "s7_decision_card_labels.user_visible_effect",
    "s7_decision_card_labels.linked_open_items",
)
_GAP_ITEM_LABEL_KEYS = (
    "s7_open_item_labels.affects_rule",
    "s7_open_item_labels.pending_or_needed",
    "s7_open_item_labels.suggested_owner",
    "s7_open_item_labels.impact_if_confirmed",
)
_MODEL_SUMMARY_LABEL_KEYS = (
    "s5_labels.first_class_objects",
    "s5_labels.object_relations",
    "s5_labels.state_machine",
)
TEMPLATE_RESIDUE_RE = re.compile(
    r"(\$1|TODO|用户可见用户可见|当[^。\n]{0,80}\.\.\.|系统应[^。\n]{0,80}\.\.\.|"
    r"进入该规则簇对应业务场景|满足来源文档定义的前置条件|以后续实现与验收规则为准)",
    re.IGNORECASE,
)
CORE_RULE_HEADING_RE = re.compile(r"^###\s*\S+", re.MULTILINE)
BOUNDARY_IN_CORE_RE = re.compile(
    r"(code style|eslint|prettier|editorconfig|hot fix|app denied|发布协作|工程协作|代码风格)",
    re.IGNORECASE,
)
DELIVERY_CONTEXT_IN_CORE_RE = re.compile(
    r"(体验版|bug\s*list|sprint|retro|grooming|planning|PR\s*review|code\s*submission|"
    r"代码每\s*\d|三方开发|甲方|乙方|项目启动时间|项目完成时间|第一阶段验收|"
    r"阶段验收|测试通过版本|走查|排期|分支合并)",
    re.IGNORECASE,
)
CODE_SPAN_RE = re.compile(r"`[^`]*`")
URL_RE = re.compile(r"https?://\S+")
LATIN_TOKEN_RE = re.compile(r"\b[A-Za-z][A-Za-z0-9]*(?:[._/+:-][A-Za-z0-9]+)*\b")
STAGE_TOKEN_RE = re.compile(r"^S[1-6]$")
HAS_CJK_RE = re.compile(r"[\u4e00-\u9fff]")
LEGACY_TERM_SOURCE_RE = re.compile(r"来源术语为\s*`?[^`。\n]+`?")
BILINGUAL_TERM_RE = re.compile(r"^\s*-\s*([^：:\n（）()]+?)（([^）]+)）[：:]")


@dataclass(frozen=True)
class ReaderLanguageCheck:
    id: str
    label: str
    severity: str
    terms: tuple[str, ...] = ()
    patterns: tuple[re.Pattern[str], ...] = ()


@dataclass(frozen=True)
class S6CheckResult:
    rel_path: str
    issues: list[str]
    warnings: list[str]


@dataclass(frozen=True)
class S6QualitySummary:
    checked: int
    issues: list[str]
    warnings: list[str]


def load_reader_language_policy(
    path: Path = DEFAULT_READER_LANGUAGE_POLICY,
) -> tuple[list[ReaderLanguageCheck], list[str]]:
    if not path.is_file():
        return [], [f"missing reader language policy `{path.relative_to(REPO_ROOT)}`"]
    try:
        policy = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [], [f"invalid reader language policy JSON: {exc}"]

    checks = policy.get("checks")
    if not isinstance(checks, list):
        return [], ["reader language policy must contain a `checks` list"]

    issues: list[str] = []
    normalized: list[ReaderLanguageCheck] = []
    for idx, check in enumerate(checks):
        if not isinstance(check, dict):
            issues.append(f"reader language policy check #{idx + 1} must be an object")
            continue

        check_id = check.get("id")
        label = check.get("label", check_id)
        severity = check.get("severity", "error")
        terms = check.get("terms", [])
        patterns = check.get("patterns", [])

        if not isinstance(check_id, str) or not check_id:
            issues.append(f"reader language policy check #{idx + 1} missing string `id`")
            continue
        if severity not in {"error", "warn"}:
            issues.append(f"reader language policy check `{check_id}` has invalid severity `{severity}`")
            continue
        if not isinstance(label, str):
            issues.append(f"reader language policy check `{check_id}` has invalid label")
            continue
        if not isinstance(terms, list) or not all(isinstance(term, str) for term in terms):
            issues.append(f"reader language policy check `{check_id}` has invalid terms")
            continue
        if not isinstance(patterns, list) or not all(isinstance(pattern, str) for pattern in patterns):
            issues.append(f"reader language policy check `{check_id}` has invalid patterns")
            continue

        compiled_patterns: list[re.Pattern[str]] = []
        check_has_invalid_pattern = False
        for pattern in patterns:
            try:
                compiled_patterns.append(re.compile(pattern))
            except re.error as exc:
                check_has_invalid_pattern = True
                issues.append(f"reader language policy check `{check_id}` has invalid pattern `{pattern}`: {exc}")
        if check_has_invalid_pattern:
            continue

        normalized.append(
            ReaderLanguageCheck(
                id=check_id,
                label=label,
                severity=severity,
                terms=tuple(terms),
                patterns=tuple(compiled_patterns),
            )
        )
    return normalized, issues


def is_final(path: Path) -> bool:
    from runtime.deliverable_locale import locale_brief_globs as _lbg
    globs = _lbg()
    suffixes = tuple(g.lstrip("*") for g in globs) if globs else ("领域知识定稿.md",)
    return any(path.name.endswith(s) for s in suffixes)


def is_pass_stub(text: str) -> bool:
    return PASS_MARKER in text[:8000]


def section(text: str, heading: str) -> str:
    if heading not in text:
        return ""
    rest = text.split(heading, 1)[1]
    next_heading = re.search(r"\n##\s+", rest)
    return rest[: next_heading.start()] if next_heading else rest


def drop_section(text: str, heading: str) -> str:
    if heading not in text:
        return text
    before, rest = text.split(heading, 1)
    next_heading = re.search(r"\n##\s+", rest)
    if not next_heading:
        return before
    return before + rest[next_heading.start() :]


def latin_tokens(text: str) -> set[str]:
    text = URL_RE.sub(" ", text)
    text = CODE_SPAN_RE.sub(" ", text)
    tokens: set[str] = set()
    for match in LATIN_TOKEN_RE.finditer(text):
        token = match.group(0).strip(".,;:()[]{}")
        if len(token) <= 1 or STAGE_TOKEN_RE.match(token):
            continue
        tokens.add(token)
    return tokens


def explained_latin_tokens(terms_section: str) -> set[str]:
    explained: set[str] = set()
    for line in terms_section.splitlines():
        if not line.lstrip().startswith("-"):
            continue
        if not HAS_CJK_RE.search(line):
            continue
        explained.update(latin_tokens(line))
        for code in CODE_SPAN_RE.findall(line):
            explained.update(LATIN_TOKEN_RE.findall(code.strip("`")))
    return explained


def bilingual_terms(terms_section: str) -> list[tuple[str, str]]:
    terms: list[tuple[str, str]] = []
    for line in terms_section.splitlines():
        match = BILINGUAL_TERM_RE.match(line)
        if not match:
            continue
        zh = match.group(1).strip()
        en = match.group(2).strip()
        if HAS_CJK_RE.search(zh) and LATIN_TOKEN_RE.search(en):
            terms.append((zh, en))
    return terms


def body_before_terms(text: str) -> str:
    if "## 术语说明" not in text:
        body = text
    else:
        body = text.split("## 术语说明", 1)[0]
    return "\n".join(line for line in body.splitlines() if not line.startswith("#"))


def bilingual_anchor_violations(text: str) -> list[str]:
    terms = section(text, "## 术语说明")
    body = body_before_terms(text)
    violations: list[str] = []
    for zh, en in bilingual_terms(terms):
        index = body.find(zh)
        if index == -1:
            continue
        expected = f"{zh}（{en}）"
        if body[index : index + len(expected)] != expected:
            violations.append(f"{zh}（{en}）")
    return violations


def core_rule_blocks(core: str) -> list[tuple[str, str]]:
    blocks: list[tuple[str, str]] = []
    matches = list(re.finditer(r"^###\s+(.+)$", core, re.MULTILINE))
    for idx, match in enumerate(matches):
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(core)
        blocks.append((match.group(1).strip(), core[start:end]))
    return blocks


def has_label(block: str, label: str) -> bool:
    label_pattern = re.compile(
        rf"^\s*-\s+(?:\*\*)?{re.escape(label)}(?:\*\*)?\s*(?:[：:].*)?$",
        re.MULTILINE,
    )
    return bool(label_pattern.search(block))


def has_layered_label(block: str, label: str) -> bool:
    layered_pattern = re.compile(
        rf"^\s*-\s+\*\*{re.escape(label)}\*\*\s*(?:[：:].*)?\n\s{{2,}}-\s+\S",
        re.MULTILINE,
    )
    return bool(layered_pattern.search(block))


def label_body(block: str, label: str) -> str:
    label_match = re.search(
        rf"^\s*-\s+\*\*{re.escape(label)}\*\*\s*(?:[：:].*)?$",
        block,
        re.MULTILINE,
    )
    if not label_match:
        return ""
    rest = block[label_match.end() :]
    next_label = re.search(r"^\s*-\s+\*\*[^*\n]+\*\*\s*(?:[：:].*)?$", rest, re.MULTILINE)
    return rest[: next_label.start()] if next_label else rest


def first_level_bullets(block: str) -> list[str]:
    bullets: list[str] = []
    for line in block.splitlines():
        match = re.match(r"^\s{2}-\s+(.+)$", line)
        if match:
            bullets.append(match.group(1).strip())
    return bullets


def dense_confirmed_rule_bullets(block: str) -> list[str]:
    from runtime.deliverable_locale import all_locale_values as _all_locale
    confirmed_labels = _all_locale("s7_decision_card_labels.confirmed_rule") or ["已确认规则"]
    confirmed = next((label_body(block, lbl) for lbl in confirmed_labels if label_body(block, lbl)), "")
    dense: list[str] = []
    for bullet in first_level_bullets(confirmed):
        if "；" in CODE_SPAN_RE.sub("", bullet):
            dense.append(bullet)
    return dense


def decision_card_violations(core: str) -> list[str]:
    from runtime.deliverable_locale import all_locale_values as _all_locale

    violations: list[str] = []
    for title, block in core_rule_blocks(core):
        missing = [
            _all_locale(key)[0] if _all_locale(key) else key.split(".")[-1]
            for key in _DECISION_CARD_LABEL_KEYS
            if not any(has_label(block, v) for v in _all_locale(key))
        ]
        if missing:
            violations.append(f"{title} missing {', '.join(missing)}")
            continue
        flat_labels = [
            _all_locale(key)[0] if _all_locale(key) else key.split(".")[-1]
            for key in _DECISION_CARD_LABEL_KEYS
            if not any(has_layered_label(block, v) for v in _all_locale(key))
        ]
        if flat_labels:
            violations.append(f"{title} labels not layered: {', '.join(flat_labels)}")
            continue
        dense_bullets = dense_confirmed_rule_bullets(block)
        if dense_bullets:
            violations.append(f"{title} has dense decision bullets: {len(dense_bullets)}")
    return violations


def delivery_context_violations(core: str) -> list[str]:
    violations: list[str] = []
    for title, block in core_rule_blocks(core):
        readable = CODE_SPAN_RE.sub(" ", block)
        hit = DELIVERY_CONTEXT_IN_CORE_RE.search(readable)
        if hit:
            violations.append(f"{title} contains delivery/collaboration context `{hit.group(0)}`")
    return violations


def key_detail_blocks(details: str) -> list[tuple[str, str]]:
    blocks: list[tuple[str, str]] = []
    matches = list(re.finditer(r"^###\s+(.+)$", details, re.MULTILINE))
    for idx, match in enumerate(matches):
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(details)
        blocks.append((match.group(1).strip(), details[start:end]))
    return blocks


def has_queryable_table(block: str) -> bool:
    lines = [line.strip() for line in block.splitlines()]
    for idx, line in enumerate(lines[:-1]):
        if not (line.startswith("|") and line.endswith("|")):
            continue
        separator = lines[idx + 1]
        if re.match(r"^\|[\s:|-]+\|$", separator):
            return True
    return False


def has_layered_list(block: str) -> bool:
    lines = block.splitlines()
    for idx, line in enumerate(lines[:-1]):
        if not re.match(r"^-\s+\S", line):
            continue
        following = "\n".join(lines[idx + 1 :])
        if re.search(r"^\s{2,}-\s+\S", following, re.MULTILINE):
            return True
    return False


def key_details_violations(text: str) -> list[str]:
    from runtime.deliverable_locale import all_locale_values as _all_locale
    key_details_variants = _all_locale("s6_s7_headings.key_details") or [KEY_DETAILS_HEADING]
    active_heading = next((v for v in key_details_variants if v in text), None)
    if not active_heading:
        return []

    details = section(text, active_heading)
    blocks = key_detail_blocks(details)
    if not blocks:
        return ["key details section must use `###` rule/detail headings"]

    violations: list[str] = []
    for title, block in blocks:
        if not block.strip():
            violations.append(f"{title} has no detail content")
            continue
        if not has_queryable_table(block) and not has_layered_list(block):
            violations.append(f"{title} must use a table or layered list")
    return violations


def _affects_rule_re() -> re.Pattern[str]:
    """Build a regex matching the 'affects rule' label in any locale."""
    from runtime.deliverable_locale import all_locale_values as _all_locale
    labels = _all_locale("s7_open_item_labels.affects_rule") or ["影响规则"]
    pattern = "|".join(re.escape(lbl) for lbl in labels)
    return re.compile(rf"^-\s+(?:\*\*)?(?:{pattern})(?:\*\*)?\s*[：:]", re.MULTILINE)


def gap_item_blocks(gaps: str) -> list[tuple[str, str]]:
    affects_re = _affects_rule_re()
    blocks: list[tuple[str, str]] = []
    current_category = ""
    current_lines: list[str] = []

    def flush() -> None:
        if current_lines:
            blocks.append((current_category, "\n".join(current_lines)))
            current_lines.clear()

    for line in gaps.splitlines():
        heading = re.match(r"^###\s+(.+?)\s*$", line)
        if heading:
            flush()
            current_category = heading.group(1).strip()
            continue
        if affects_re.match(line):
            flush()
            current_lines.append(line)
            continue
        if current_lines:
            current_lines.append(line)
    flush()
    return blocks


def gap_index_violations(gaps: str) -> list[str]:
    from runtime.deliverable_locale import all_locale_values as _all_locale

    violations: list[str] = []
    for current_category, block in gap_item_blocks(gaps):
        missing = [
            _all_locale(key)[0] if _all_locale(key) else key.split(".")[-1]
            for key in _GAP_ITEM_LABEL_KEYS
            if not any(has_label(block, v) for v in _all_locale(key))
        ]
        if missing:
            item = block.splitlines()[0].lstrip()[1:].strip()
            preview = item[:40] + ("..." if len(item) > 40 else "")
            prefix = f"{current_category}: " if current_category else ""
            violations.append(f"{prefix}{preview} missing {', '.join(missing)}")
            continue
        # Layered check: all labels after the first must use **label**: format.
        layered = all(
            any(
                re.search(rf"^\s{{2,}}-\s+\*\*{re.escape(v)}\*\*\s*[：:]", block, re.MULTILINE)
                for v in _all_locale(key)
            )
            for key in _GAP_ITEM_LABEL_KEYS[1:]
        )
        if not layered:
            item = block.splitlines()[0].lstrip()[1:].strip()
            preview = item[:40] + ("..." if len(item) > 40 else "")
            prefix = f"{current_category}: " if current_category else ""
            violations.append(f"{prefix}{preview} action item labels not layered")
    return violations


def unexplained_latin_terms(text: str) -> set[str]:
    terms = section(text, "## 术语说明")
    explained = explained_latin_tokens(terms)
    body = drop_section(text, "## 术语说明")
    body = drop_section(body, "## 溯源")
    return latin_tokens(body) - explained


def reader_language_hits(
    text: str,
    checks: list[ReaderLanguageCheck],
) -> tuple[list[str], list[str]]:
    readable_text = URL_RE.sub(" ", CODE_SPAN_RE.sub(" ", text))
    error_hits: list[str] = []
    warn_hits: list[str] = []
    for check in checks:
        terms = [term for term in check.terms if term in readable_text]
        patterns = [pattern.pattern for pattern in check.patterns if pattern.search(readable_text)]
        if not terms and not patterns:
            continue
        preview_parts = terms + [f"/{pattern}/" for pattern in patterns]
        preview = f"{check.label}: {', '.join(preview_parts[:8])}"
        if len(preview_parts) > 8:
            preview += f" (+{len(preview_parts) - 8} more)"
        if check.severity == "warn":
            warn_hits.append(preview)
        else:
            error_hits.append(preview)
    return error_hits, warn_hits


def check_s6_text(
    text: str,
    rel_path: str,
    reader_language_checks: list[ReaderLanguageCheck],
    *,
    requires_key_details: bool = False,
) -> S6CheckResult:
    from runtime.deliverable_locale import all_locale_values as _all_locale

    if is_pass_stub(text):
        return S6CheckResult(rel_path=rel_path, issues=[], warnings=[])

    issues: list[str] = []
    warnings: list[str] = []

    # Required sections — accept any locale's heading.
    for section_key in _S6_REQUIRED_SECTION_KEYS:
        variants = _all_locale(section_key)
        if not any(v in text for v in variants):
            display = variants[0] if variants else section_key
            issues.append(f"{rel_path}: missing required S6 reader section `{display}`")

    if TEMPLATE_RESIDUE_RE.search(text):
        issues.append(f"{rel_path}: contains template residue or truncated generated sentence")

    reader_language_errors, reader_language_warnings = reader_language_hits(text, reader_language_checks)
    for hit in reader_language_errors:
        issues.append(f"{rel_path}: reader language policy violation: {hit}")
    for hit in reader_language_warnings:
        warnings.append(f"{rel_path}: reader language policy warning: {hit}")

    # Core business rules section — try all locale headings.
    core_variants = _all_locale("s6_s7_headings.core_business_rules")
    core = next((section(text, h) for h in core_variants if section(text, h)), "")
    if core and not CORE_RULE_HEADING_RE.search(core):
        issues.append(f"{rel_path}: core business rules must contain reader-facing `###` rule/topic headings")
    if core and BOUNDARY_IN_CORE_RE.search(core):
        issues.append(f"{rel_path}: boundary/noise material appears in core business rules")
    if core:
        delivery_context_issues = delivery_context_violations(core)
        if delivery_context_issues:
            preview = "; ".join(delivery_context_issues[:6])
            suffix = "" if len(delivery_context_issues) <= 6 else f" (+{len(delivery_context_issues) - 6} more)"
            issues.append(f"{rel_path}: delivery/collaboration material appears in core business rules: {preview}{suffix}")
    if core:
        decision_card_issues = decision_card_violations(core)
        if decision_card_issues:
            preview = "; ".join(decision_card_issues[:6])
            suffix = "" if len(decision_card_issues) <= 6 else f" (+{len(decision_card_issues) - 6} more)"
            issues.append(f"{rel_path}: core rules reader-structure issues: {preview}{suffix}")

    # Key details section — accept any locale heading.
    key_details_variants = _all_locale("s6_s7_headings.key_details")
    active_kd_heading = next((v for v in key_details_variants if v in text), None)
    detail_issues = key_details_violations(text)
    if requires_key_details and not active_kd_heading:
        issues.append(f"{rel_path}: missing `{KEY_DETAILS_HEADING}` required by S5 structured detail handoff")
    if detail_issues:
        preview = "; ".join(detail_issues[:6])
        suffix = "" if len(detail_issues) <= 6 else f" (+{len(detail_issues) - 6} more)"
        issues.append(f"{rel_path}: key details section is not queryable: {preview}{suffix}")

    # Domain model summary — accept any locale heading and label.
    model_variants = _all_locale("s6_s7_headings.domain_model_summary")
    model_summary = next((section(text, h) for h in model_variants if section(text, h)), "")
    for label_key in _MODEL_SUMMARY_LABEL_KEYS:
        label_variants = _all_locale(label_key)
        display_label = label_variants[0] if label_variants else label_key.split(".")[-1]
        if model_summary and not any(has_label(model_summary, v) for v in label_variants):
            issues.append(f"{rel_path}: domain model summary missing `{display_label}`")
        elif model_summary and not any(has_layered_label(model_summary, v) for v in label_variants):
            issues.append(f"{rel_path}: domain model summary label `{display_label}` is not layered")

    # Open items (gap) section — accept any locale heading.
    open_items_variants = _all_locale("s6_s7_headings.open_items")
    gaps = next((section(text, h) for h in open_items_variants if section(text, h)), "")
    if gaps:
        missing_categories = [cat for cat in GAP_CATEGORIES if f"### {cat}" not in gaps]
        if missing_categories:
            issues.append(f"{rel_path}: gap section missing categories: {', '.join(missing_categories)}")
        gap_index_issues = gap_index_violations(gaps)
        if gap_index_issues:
            preview = "; ".join(gap_index_issues[:6])
            suffix = "" if len(gap_index_issues) <= 6 else f" (+{len(gap_index_issues) - 6} more)"
            issues.append(f"{rel_path}: gap items missing action-index labels: {preview}{suffix}")

    # Glossary section — accept any locale heading.
    glossary_variants = _all_locale("s6_s7_headings.glossary")
    terms = next((section(text, h) for h in glossary_variants if section(text, h)), "")
    if LEGACY_TERM_SOURCE_RE.search(terms):
        issues.append(f"{rel_path}: terms should use `中文术语（English Term）` anchors, not legacy `来源术语为 ...` wording")

    missing_anchors = bilingual_anchor_violations(text)
    if missing_anchors:
        preview = ", ".join(missing_anchors[:8])
        suffix = "" if len(missing_anchors) <= 8 else f" (+{len(missing_anchors) - 8} more)"
        issues.append(f"{rel_path}: first body occurrence missing bilingual term anchor: {preview}{suffix}")

    unexplained_latin = sorted(unexplained_latin_terms(text), key=str.lower)
    if unexplained_latin:
        preview = ", ".join(unexplained_latin[:12])
        suffix = "" if len(unexplained_latin) <= 12 else f" (+{len(unexplained_latin) - 12} more)"
        issues.append(f"{rel_path}: unexplained English terms in S6 body: {preview}{suffix}")

    return S6CheckResult(rel_path=rel_path, issues=issues, warnings=warnings)


def check_s6_file(path: Path, reader_language_checks: list[ReaderLanguageCheck]) -> S6CheckResult:
    rel_path = path.relative_to(REPO_ROOT).as_posix()
    text = path.read_text(encoding="utf-8", errors="replace")
    return check_s6_text(
        text,
        rel_path,
        reader_language_checks,
        requires_key_details=sibling_s5_has_structured_detail_handoff(path),
    )


def sibling_s5_has_structured_detail_handoff(final_path: Path) -> bool:
    from runtime.deliverable_locale import all_locale_values as _all_locale, work_draft_globs as _wdg
    struct_variants = _all_locale("s5_headings.structured_detail") or [S5_STRUCTURED_DETAIL_HEADING]
    seen: set[Path] = set()
    for glob_pat in _wdg():
        for candidate in sorted(final_path.parent.glob(glob_pat)):
            if candidate in seen:
                continue
            seen.add(candidate)
            try:
                text = candidate.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if any(h in text for h in struct_variants):
                return True
    return False


def iter_final_drafts(root_id: str | None = None) -> list[Path]:
    paths: list[Path] = []
    for root in sorted(DISTILLED_BY_ROOT.iterdir()):
        if not root.is_dir():
            continue
        if root_id and root.name != root_id:
            continue
        paths.extend(md for md in sorted(root.rglob("*.md")) if is_final(md))
    return paths


def run_s6_reader_quality(root_id: str | None = None) -> S6QualitySummary:
    issues: list[str] = []
    warnings: list[str] = []
    if not DISTILLED_BY_ROOT.is_dir():
        return S6QualitySummary(checked=0, issues=[f"Missing curated tree: {DISTILLED_BY_ROOT}"], warnings=[])

    reader_language_checks, policy_issues = load_reader_language_policy()
    issues.extend(policy_issues)

    checked = 0
    for md in iter_final_drafts(root_id):
        checked += 1
        result = check_s6_file(md, reader_language_checks)
        issues.extend(result.issues)
        warnings.extend(result.warnings)
    return S6QualitySummary(checked=checked, issues=issues, warnings=warnings)
