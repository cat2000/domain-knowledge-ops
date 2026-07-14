#!/usr/bin/env python3
"""Prep tagging-acceptance report (S2 pause) + optional post-S3 exhaustiveness.

Industry module cuts are question axes only. Bidirectional tagging is complete only when
every accepted source has a closure landing and humans confirm using this report — not
the module table alone.

Usage:
  python3 scripts/distill/tagging_acceptance.py --root-id <R>
  python3 scripts/distill/tagging_acceptance.py --root-id <R> --after-s3
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
    # _deliver/<slug>/... or appendix-like
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


def _s7_rule_count(curated: Path, slug: str) -> int | None:
    deliver = curated / "_deliver" / slug
    if not deliver.is_dir():
        return None
    from runtime.deliverable_locale import resolve_locale_brief_path

    brief = resolve_locale_brief_path(deliver, slug)
    if brief is None or not brief.is_file():
        return None
    text = brief.read_text(encoding="utf-8", errors="replace")
    return len(re.findall(r"^###\s+(规则|Rule)\s*\d+", text, re.MULTILINE))


def report(root_id: str, *, after_s3: bool) -> int:
    curated = CURATED_BY_ROOT / root_id
    checklist = curated / "DOMAIN_MODULE_CHECKLIST.md"
    lines: list[str] = []
    lines.append(f"# Tagging acceptance · root `{root_id}`")
    lines.append("")
    lines.append(
        "Industry module cuts are **question axes**. Completeness requires bidirectional "
        "tagging (closure) + this report before confirm — not the strategy table alone."
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

    modules = []
    if checklist.is_file():
        modules = parse_checklist_modules(checklist.read_text(encoding="utf-8", errors="replace"))
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
        lines.append(f"| `{mod.slug}` | {st} | {n} | {advice} |")
    lines.append("")

    lines.append("## Actions before human confirm")
    lines.append("1. Do **not** tell the user to confirm every row.")
    lines.append("2. Zero-source rows (**must** stay pending): " + (", ".join(f"`{s}`" for s in zero_source) or "_none_"))
    lines.append("3. Low-source rows (optional confirm): " + (", ".join(f"`{s}`" for s in low_source) or "_none_"))
    lines.append("4. Confirm candidates: " + (", ".join(f"`{s}`" for s in confirm_ok) or "_none_"))
    if jira_n == 0:
        lines.append("5. Recommend Jira ingest+classify before compose when `board_id` is set.")
    lines.append("")

    if after_s3:
        lines.append("## Post-S3 exhaustiveness (compose)")
        lines.append("| slug | closure | pages_total | pages_with_props | S7 rules | note |")
        lines.append("|------|---------|-------------|------------------|----------|------|")
        for mod in modules:
            if not mod.slug or not _is_confirmed(mod.status):
                continue
            slug = mod.slug
            n = slug_counts.get(slug, 0)
            pt, pwp = _props_summary(curated, slug)
            rules = _s7_rule_count(curated, slug)
            note = ""
            if pwp is not None and pwp == 0:
                note = "no props — do not ship as committed S7"
            elif pt is not None and pwp is not None and pt > 0 and pwp < max(1, pt // 3):
                note = "many pages lack props — check open items / remount"
            elif rules is not None and pwp is not None and pwp > 0 and rules < max(1, pwp // 10):
                note = "rule count << pages_with_props — possible under-write; list gaps in Open items"
            elif rules is None and _is_confirmed(mod.status):
                note = "S7 not written yet"
            lines.append(
                f"| `{slug}` | {n} | {pt if pt is not None else '—'} | "
                f"{pwp if pwp is not None else '—'} | {rules if rules is not None else '—'} | {note} |"
            )
        lines.append("")
        lines.append(
            "Do **not** claim a module is fully covered when notes show under-write; "
            "record residual sources in S7 Open items or leave pending."
        )
        lines.append("")

    out = curated / "TAGGING_ACCEPTANCE.md"
    text = "\n".join(lines).rstrip() + "\n"
    out.write_text(text, encoding="utf-8")
    print(text)
    print(f"(wrote {out.relative_to(REPO_ROOT)})")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="S2 tagging acceptance / post-S3 exhaustiveness report")
    p.add_argument("--root-id", required=True)
    p.add_argument(
        "--after-s3",
        action="store_true",
        help="Also compare closure vs propositions.json vs S7 rule counts for confirmed slugs",
    )
    args = p.parse_args()
    return report(str(args.root_id).strip(), after_s3=bool(args.after_s3))


if __name__ == "__main__":
    raise SystemExit(main())
