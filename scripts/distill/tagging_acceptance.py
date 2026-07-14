#!/usr/bin/env python3
"""Prep tagging-acceptance + compose exhaustiveness (industry axes kept).

Industry module cuts stay as adjudication axes. Product-surface wiki pages must be
*remounted* into those axes (not reintroduced as Mall/Hui/Gateway modules).

Usage:
  python3 scripts/distill/tagging_acceptance.py --root-id <R>
  python3 scripts/distill/tagging_acceptance.py --root-id <R> --after-s3
  python3 scripts/distill/tagging_acceptance.py --root-id <R> --after-s7
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

_SCRIPTS = next(p for p in Path(__file__).resolve().parents if (p / "_install.py").is_file())
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
import _install

_install.bootstrap(__file__)

from distill._paths import CURATED_BY_ROOT, MATERIALIZED_BY_ROOT, REPO_ROOT, resolve_closure_file
from runtime.checklist_modules import parse_checklist_modules
from runtime.deliverable_locale import all_locale_values

# Keep industry axes; remount product-surface evidence into them.
REMOUNT_HINTS: list[tuple[str, str]] = [
    ("Mall catalog / cart / first-order / IOR coupon", "ordering-fulfillment (or membership if eligibility-only)"),
    ("Checkout session / node / FPV / pending-pay / promo hold", "ordering-fulfillment"),
    ("Hui shell / CBP cards / Pacesetter UI", "membership-eligibility and/or compensation-performance"),
    ("Milestone / Super Expanding Star / contest matrices", "compensation-performance (do not drop after remount)"),
    ("Privacy gate / password reset / rebind phone / title map", "membership-eligibility (or a confirmed new identity slug)"),
    ("In-app message center / read-unread / business templates", "ordering-fulfillment or membership if user-visible; else Open items — do not invent messaging module unless strategy confirms"),
    ("Gateway auth / SDK-only", "appendix / non-business unless it changes a user-visible commitment"),
    ("Autoship plan rules", "autoship-renewal — keep pending until tagged sources exist"),
    ("Returns / quality complaints", "returns-quality — confirm only when business rules exist; else pending"),
]


def _is_confirmed(status: str) -> bool:
    value = str(status or "").strip()
    return bool(value) and value in set(all_locale_values("checklist.status_confirmed"))


def _closure_targets(curated: Path) -> dict[str, list[str]]:
    path = resolve_closure_file(curated)
    if path is None or not path.is_file():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    if not isinstance(raw, dict):
        return {}
    out: dict[str, list[str]] = {}
    for src, dest in raw.items():
        if str(src).startswith("_"):
            continue
        if isinstance(dest, str):
            out[str(src)] = [dest]
        elif isinstance(dest, list):
            out[str(src)] = [str(x) for x in dest]
        else:
            out[str(src)] = []
    return out


def _slug_from_target(target: str) -> str | None:
    m = re.match(r"^_deliver/([^/]+)/", target.replace("\\", "/"))
    if m:
        return m.group(1)
    if "_附录" in target or "appendix" in target.lower() or "非业务" in target:
        return None
    return None


def _count_materialized_md(root_id: str) -> int:
    root = MATERIALIZED_BY_ROOT / root_id
    if not root.is_dir():
        return 0
    return sum(1 for p in root.rglob("*.md") if p.name != "README.md")


def _jira_attribution_count(curated: Path) -> int:
    attr = curated / "jira" / "attribution"
    if not attr.is_dir():
        return 0
    return sum(1 for _ in attr.glob("*.yaml")) + sum(1 for _ in attr.glob("*.yml"))


def _props_summary(curated: Path, slug: str) -> tuple[int | None, int | None]:
    path = curated / "_aggregate" / slug / f"{slug}-propositions.json"
    if not path.is_file():
        return None, None
    raw = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    if not isinstance(raw, dict):
        return None, None
    return (
        int(raw.get("pages_total") or 0),
        int(raw.get("pages_with_props") or 0),
    )


def _s7_meta(curated: Path, slug: str) -> tuple[int | None, bool]:
    """Return (rule_count, has_insufficiency_banner)."""
    deliver = curated / "_deliver" / slug
    if not deliver.is_dir():
        return None, False
    from runtime.deliverable_locale import resolve_locale_brief_path

    brief = resolve_locale_brief_path(deliver, slug)
    if brief is None or not brief.is_file():
        return None, False
    text = brief.read_text(encoding="utf-8", errors="replace")
    rules = len(re.findall(r"^###\s+(规则|Rule)\s*\d+", text, re.MULTILINE))
    banner = bool(
        re.search(r"Evidence insufficiency|证据不足", text, re.IGNORECASE)
    )
    return rules, banner


def _underwrite_note(
    *,
    pwp: int | None,
    pt: int | None,
    rules: int | None,
    banner: bool,
    require_s7: bool,
) -> str:
    if pwp is not None and pwp == 0:
        return "FAIL — pages_with_props=0; revert confirm / do not ship committed S7"
    if require_s7 and rules is not None and rules == 0 and (pwp or 0) > 0:
        return "FAIL — confirmed with sources but zero ### 规则/Rule; revert or rewrite (fake coverage)"
    if require_s7 and rules is not None and rules == 0 and not banner:
        return "FAIL — zero rules and no Evidence insufficiency banner"
    if pt is not None and pwp is not None and pt > 0 and pwp < max(1, pt // 3):
        return "WARN — many pages lack props; remount / Open items"
    if (
        rules is not None
        and pwp is not None
        and pwp >= 10
        and rules < max(2, pwp // 20)
    ):
        return (
            "WARN — under-write (rules << pages_with_props); "
            "remount product-surface evidence into this axis or list Open items"
        )
    if require_s7 and rules is None:
        return "S7 not written yet"
    if banner:
        return "OK-ish — insufficiency banner present (non-SSOT for risk)"
    return "OK"


def report(root_id: str, *, after_s3: bool, after_s7: bool, strict: bool) -> int:
    curated = CURATED_BY_ROOT / root_id
    checklist = curated / "DOMAIN_MODULE_CHECKLIST.md"
    lines: list[str] = []
    fail_flags: list[str] = []

    lines.append(f"# Tagging acceptance · root `{root_id}`")
    lines.append("")
    lines.append(
        "Keep **industry adjudication axes**. Completeness = remount product-surface "
        "evidence into those axes + bidirectional tagging + write-through to S7 — "
        "not the strategy table alone, and not reintroducing Mall/Hui/Gateway as modules."
    )
    lines.append("")

    if not curated.is_dir():
        print(f"ERROR: missing curated root {curated}", file=sys.stderr)
        return 2

    closure = _closure_targets(curated)
    mat_count = _count_materialized_md(root_id)
    closed = len(closure)
    uncovered_hint = max(0, mat_count - closed) if mat_count else 0

    slug_counts: Counter[str] = Counter()
    appendix = 0
    unmapped_dest = 0
    for _src, dests in closure.items():
        if not dests:
            unmapped_dest += 1
            continue
        for d in dests:
            slug = _slug_from_target(d)
            if slug:
                slug_counts[slug] += 1
            else:
                appendix += 1

    jira_n = _jira_attribution_count(curated)
    lines.append("## Corpus")
    lines.append(f"- Materialized `.md` (approx): **{mat_count}**")
    lines.append(f"- Closure source entries: **{closed}**")
    if mat_count and closed:
        pct = min(100.0, 100.0 * closed / mat_count)
        lines.append(f"- Closure vs materialized (rough): **{pct:.0f}%** entries tagged")
    if uncovered_hint and mat_count > closed:
        lines.append(
            f"- WARNING: materialized count exceeds closure keys by ~{uncovered_hint} "
            "(re-run S2 gap-fill / check unmatched)"
        )
    lines.append(f"- Closure → `_deliver/<slug>/`: **{sum(slug_counts.values())}**")
    lines.append(f"- Closure → appendix / non-business: **{appendix}**")
    if unmapped_dest:
        lines.append(f"- Closure rows with empty destination: **{unmapped_dest}**")
    lines.append("")

    lines.append("## Jira half of bidirectional tagging")
    if jira_n == 0:
        lines.append(
            "- **INCOMPLETE**: `jira/attribution` count = **0**. "
            "With a configured `board_id`, run `@add-knowledge-from-jira team=<key>` "
            "before treating tagging as complete (wiki-only = half corpus)."
        )
    else:
        lines.append(f"- Jira attribution files: **{jira_n}**")
    lines.append("")

    lines.append("## Remount hints (keep industry axes)")
    lines.append(
        "Do **not** recreate product-surface modules. Map dense wiki themes into confirmed axes:"
    )
    for src, dest in REMOUNT_HINTS:
        lines.append(f"- {src} → **{dest}**")
    lines.append("")

    modules = []
    if checklist.is_file():
        modules = parse_checklist_modules(
            checklist.read_text(encoding="utf-8", errors="replace")
        )
    else:
        lines.append("WARNING: `DOMAIN_MODULE_CHECKLIST.md` missing")
        lines.append("")

    zero_source: list[str] = []
    low_source: list[str] = []
    confirm_ok: list[str] = []
    lines.append("## Per-module (confirm gate)")
    lines.append("| slug | status | closure→deliver | confirm? |")
    lines.append("|------|--------|-----------------|----------|")
    for mod in modules:
        if not mod.slug:
            continue
        n = slug_counts.get(mod.slug, 0)
        st = mod.status
        if n <= 0:
            advice = "NO — keep pending (zero tagged sources)"
            zero_source.append(mod.slug)
        elif n < 3:
            advice = "LOW evidence — confirm only if intentional; S7 needs insufficiency banner"
            low_source.append(mod.slug)
        else:
            advice = "OK to confirm if cut is accepted"
            confirm_ok.append(mod.slug)
        if _is_confirmed(st) and n <= 0:
            advice = "FAIL — confirmed but zero sources (revert to pending)"
            fail_flags.append(f"{mod.slug}: confirmed with zero sources")
        lines.append(f"| `{mod.slug}` | {st} | {n} | {advice} |")
    lines.append("")

    lines.append("## Actions before human confirm")
    lines.append("1. Do **not** tell the user to confirm every row.")
    lines.append(
        "2. Zero-source rows (**must** stay pending): "
        + (", ".join(f"`{s}`" for s in zero_source) or "_none_")
    )
    lines.append(
        "3. Low-source rows (optional confirm): "
        + (", ".join(f"`{s}`" for s in low_source) or "_none_")
    )
    lines.append(
        "4. Confirm candidates: " + (", ".join(f"`{s}`" for s in confirm_ok) or "_none_")
    )
    if jira_n == 0:
        lines.append("5. Recommend Jira ingest+classify before compose when `board_id` is set.")
    lines.append(
        "6. Remount Mall/Hui/checkout/contest/identity surfaces into industry axes "
        "(see hints) — do not add those as new default modules."
    )
    lines.append("")

    if after_s3 or after_s7:
        require_s7 = after_s7
        title = "Post-S7 write-through" if after_s7 else "Post-S3 exhaustiveness"
        lines.append(f"## {title}")
        lines.append(
            "| slug | closure | pages_total | pages_with_props | S7 rules | note |"
        )
        lines.append(
            "|------|---------|-------------|------------------|----------|------|"
        )
        for mod in modules:
            if not mod.slug or not _is_confirmed(mod.status):
                continue
            slug = mod.slug
            n = slug_counts.get(slug, 0)
            pt, pwp = _props_summary(curated, slug)
            rules, banner = _s7_meta(curated, slug)
            note = _underwrite_note(
                pwp=pwp, pt=pt, rules=rules, banner=banner, require_s7=require_s7
            )
            if note.startswith("FAIL"):
                fail_flags.append(f"{slug}: {note}")
            lines.append(
                f"| `{slug}` | {n} | {pt if pt is not None else '—'} | "
                f"{pwp if pwp is not None else '—'} | "
                f"{rules if rules is not None else '—'} | {note} |"
            )
        lines.append("")
        lines.append(
            "**Write-through rule:** tagged sources with business propositions must become "
            "`### 规则` / `### Rule` cards or explicit Open items. "
            "Confirmed + sources + zero rules = **fake coverage** — revert confirm."
        )
        lines.append(
            "Under-write: remount leftover product-surface evidence into this axis, "
            "or list residual pages in Open items — do not claim fully covered."
        )
        lines.append("")

    if fail_flags:
        lines.append("## Gate failures")
        for f in fail_flags:
            lines.append(f"- {f}")
        lines.append("")

    out = curated / "TAGGING_ACCEPTANCE.md"
    text = "\n".join(lines).rstrip() + "\n"
    out.write_text(text, encoding="utf-8")
    print(text)
    try:
        print(f"(wrote {out.relative_to(REPO_ROOT)})")
    except ValueError:
        print(f"(wrote {out})")

    if strict and fail_flags:
        return 1
    return 0


def main() -> int:
    p = argparse.ArgumentParser(
        description="S2 tagging acceptance / compose exhaustiveness (industry axes)"
    )
    p.add_argument("--root-id", required=True)
    p.add_argument(
        "--after-s3",
        action="store_true",
        help="Compare closure vs propositions; warn under-write / zero props",
    )
    p.add_argument(
        "--after-s7",
        action="store_true",
        help="Also require S7 rule write-through (fail confirmed+sources+zero rules)",
    )
    p.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 when FAIL rows are present",
    )
    args = p.parse_args()
    return report(
        str(args.root_id).strip(),
        after_s3=bool(args.after_s3),
        after_s7=bool(args.after_s7),
        strict=bool(args.strict),
    )


if __name__ == "__main__":
    raise SystemExit(main())
