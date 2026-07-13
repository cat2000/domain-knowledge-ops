"""Canonical paths and naming for domain-knowledge layout (SSOT)."""

from __future__ import annotations

import re
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = SCRIPTS_DIR.parent
DOMAIN_KNOWLEDGE = REPO_ROOT / "domain-knowledge"

DIR_MATERIALIZED = "materialized"
DIR_CURATED = "curated"
DIR_EXTRACTED = "extracted"

MATERIALIZED_BY_ROOT = DOMAIN_KNOWLEDGE / DIR_MATERIALIZED / "by-root"
CURATED_BY_ROOT = DOMAIN_KNOWLEDGE / DIR_CURATED / "by-root"
EXTRACTED_BY_ROOT = DOMAIN_KNOWLEDGE / DIR_EXTRACTED / "by-root"

FACET_UNMATCHED = "facet-unmatched"
FACET_MISC = "facet-misc"
FACET_CHECKOUT = "facet-checkout"
FACET_GATEWAY = "facet-gateway"
FACET_COMPENSATION_CBP = "facet-compensation-cbp"
FACET_CONTESTS = "facet-contests"
FACET_MESSAGING = "facet-messaging"
FACET_COMPLIANCE_IDENTITY = "facet-compliance-identity"

FACET_DIRS = frozenset(
    {
        FACET_UNMATCHED,
        FACET_MISC,
        FACET_CHECKOUT,
        FACET_GATEWAY,
        FACET_COMPENSATION_CBP,
        FACET_CONTESTS,
        FACET_MESSAGING,
        FACET_COMPLIANCE_IDENTITY,
    }
)

# Pre-facet-refactor folder names — must not appear under materialized/by-root/<R>/.
FORBIDDEN_MATERIALIZED_TOP_DIRS = frozenset(
    {
        "routing-pending",
        "requirements",
        "checkout",
        "gateway",
        "compensation-cbp",
        "contests",
        "messaging",
        "compliance-identity",
    }
)

DOMAIN_MODULE_CHECKLIST_FILE = "DOMAIN_MODULE_CHECKLIST.md"
MATERIALIZATION_CLOSURE_FILE = "_materialization_closure.json"

NON_BUSINESS_HEADING = "## 非业务判定（Cursor）"
PASS_HEADINGS = frozenset({NON_BUSINESS_HEADING})

CHECKLIST_STATUS_PENDING = "待确认"
CHECKLIST_STATUS_CONFIRMED = "确认"

# English-locale equivalents accepted by validators (case-insensitive compact match).
_EN_STATUS_CONFIRMED_TOKENS = frozenset({"confirmed", "confirm"})
_EN_STATUS_PENDING_TOKENS = frozenset({"pending"})


def is_checklist_status_confirmed(status: str) -> bool:
    """True for explicit 确认 / confirmed; 待确认 / pending must NOT match."""
    raw = status.strip()
    if not raw or raw in ("—", "-", "不归档", "未开始"):
        return False
    # Pending guard (zh + en) — must come before confirmed check.
    if CHECKLIST_STATUS_PENDING in raw:
        return False
    lower_compact = raw.replace("*", "").strip().lower()
    if lower_compact in _EN_STATUS_PENDING_TOKENS:
        return False
    # Confirmed check (zh).
    compact = raw.replace("*", "").strip()
    if compact == CHECKLIST_STATUS_CONFIRMED:
        return True
    if f"**{CHECKLIST_STATUS_CONFIRMED}**" in status:
        return True
    # Confirmed check (en).
    if lower_compact in _EN_STATUS_CONFIRMED_TOKENS:
        return True
    return False


_CHECKLIST_SLUG_RE = re.compile(r"（([^）]+)）")
_DELIVER_SLUG_RE = re.compile(r"_deliver/([a-z0-9-]+)/")


def slug_from_checklist_columns(cols: list[str]) -> str | None:
    """Prefer _deliver/<slug>/ in 主入口; else last （slug） in 主题."""
    if len(cols) >= 4:
        m = _DELIVER_SLUG_RE.search(cols[3])
        if m:
            return m.group(1)
    if cols:
        matches = _CHECKLIST_SLUG_RE.findall(cols[0])
        if matches:
            return matches[-1].strip()
    return None


def confirmed_slugs_from_checklist(text: str) -> list[str]:
    """Return slugs whose checklist module/row status is 确认."""
    from runtime.checklist_modules import confirmed_slugs_from_checklist as _impl

    return _impl(text)

S2_LABEL = "认域·打标"


def materialized_repo_rel(root_id: str, rel_posix: str) -> str:
    return f"domain-knowledge/{DIR_MATERIALIZED}/by-root/{root_id}/{rel_posix}"


def curated_repo_rel(root_id: str, *parts: str) -> str:
    tail = "/".join(parts)
    return f"domain-knowledge/{DIR_CURATED}/by-root/{root_id}/{tail}"


def resolve_closure_file(curated_root: Path) -> Path | None:
    p = curated_root / MATERIALIZATION_CLOSURE_FILE
    return p if p.is_file() else None


def resolve_checklist_file(curated_root: Path) -> Path | None:
    p = curated_root / DOMAIN_MODULE_CHECKLIST_FILE
    return p if p.is_file() else None
