#!/usr/bin/env python3
"""
Verify every domain-knowledge/materialized/by-root/<根ID>/*.md has a covering curated artifact.

Two modes per root (auto-detected):

1. **Source closure** — if ``curated/by-root/<根ID>/_materialization_closure.json`` exists:
   JSON object maps each ``materialized`` relative path (POSIX) to one or more ``curated``
   paths (string or list of strings, relative to that distilled root). Used when stage-2
   organizes **domain-first** (paths need not mirror ``materialized/``).

2. **Legacy same-path** — otherwise each ``materialized`` ``*.md`` must exist at the **same relative path**
   under ``curated/by-root/<根ID>/``.

README.md under materialized is skipped (documentation only).

Count **Pass stubs** (## 非业务判定（Cursor） in file head) vs **full** drafts — missing=0 only means
**closure**, not that Chinese domain distill (stage 2) is done.

Exit code: 0 if no gaps (after excludes), 1 otherwise.

Optional excludes:
  - Repeatable --exclude-prefix (relative to each root's tree, e.g. facet-unmatched/)
  - --exclude-file PATH — one prefix per line (# comments allowed)

Strict modes (optional):
  - --fail-if-all-pass-stubs: fail when every distilled file is a Pass stub (no non-Pass drafts).
  - --fail-if-any-pass-stub: fail when any checked path is still a Pass stub (full-tree semantic gate).
  - --fail-if-pass-stub-ratio-above R: fail when pass_stubs/checked > R (e.g. 0.99).

Use --warn-only to print gaps but always exit 0 (local exploration).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SCRIPTS = next(p for p in Path(__file__).resolve().parents if (p / "_install.py").is_file())
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
import _install

_install.bootstrap(__file__)

from distill._exclude import is_excluded, load_exclude_prefixes
from distill._paths import (
    DISTILLED_BY_ROOT,
    PASS_HEADINGS,
    REPO_ROOT,
    RULES_BY_ROOT,
    SOURCE_CLOSURE_FILE,
)
from distill.coverage_logic import (
    evaluate_strict_violations,
    looks_like_pass_stub_file,
    normalize_closure_value,
    rules_only_pass_ratio,
)

def main() -> int:
    parser = argparse.ArgumentParser(description="Check rules → curated path coverage.")
    parser.add_argument(
        "--root-id",
        help="Only check this Confluence root page ID directory (e.g. 48693262).",
    )
    parser.add_argument(
        "--exclude-prefix",
        action="append",
        default=[],
        metavar="PREFIX",
        help="Skip rules files whose relative path starts with this prefix (repeatable). "
        "Trailing slash optional; normalized to end with '/'.",
    )
    parser.add_argument(
        "--exclude-file",
        type=Path,
        default=None,
        metavar="PATH",
        help="File of exclude prefixes (one per line; # comments allowed).",
    )
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Print gaps but exit 0.",
    )
    parser.add_argument(
        "--fail-if-all-pass-stubs",
        action="store_true",
        help=(
            "Exit 1 when checked>0 and every matching distilled file is a Pass stub "
            "(## 非业务判定（Cursor）). Use to catch 'only stage-1 + placeholders' trees."
        ),
    )
    parser.add_argument(
        "--fail-if-any-pass-stub",
        action="store_true",
        help=(
            "Exit 1 when pass_stubs>0 for checked paths (every rules file must have non-Pass "
            "curated). Full gate after RUNBOOK S5; S2 needs closure mapping only."
        ),
    )
    parser.add_argument(
        "--fail-if-pass-stub-ratio-above",
        type=float,
        default=None,
        metavar="R",
        help=(
            "Exit 1 when pass_stubs/checked > R (0<R<=1). Example: 0.99 fails if almost "
            "all distilled files are still Pass stubs."
        ),
    )
    parser.add_argument(
        "--quiet-pass-note",
        action="store_true",
        help="Do not print the stderr note explaining Pass stubs vs domain distill.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable summary to stdout (still prints human lines unless --json-only).",
    )
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Only print JSON (implies --json).",
    )
    args = parser.parse_args()
    json_only = args.json_only
    if json_only:
        args.json = True

    if not RULES_BY_ROOT.is_dir():
        print(f"Missing rules tree: {RULES_BY_ROOT}", file=sys.stderr)
        return 0 if args.warn_only else 1

    exclude_prefixes: list[str] = []
    if args.exclude_file and args.exclude_file.is_file():
        exclude_prefixes.extend(load_exclude_prefixes(args.exclude_file))
    for raw in args.exclude_prefix:
        p = raw.strip()
        if not p:
            continue
        if not p.endswith("/"):
            p = p + "/"
        exclude_prefixes.append(p)

    missing: list[dict[str, str]] = []
    checked = 0
    skipped_readme = 0
    skipped_excluded = 0
    pass_stubs = 0
    full_files = 0
    rules_with_only_pass_distill = 0
    roots_using_closure: list[str] = []

    root_dirs = sorted(RULES_BY_ROOT.iterdir())
    for root_dir in root_dirs:
        if not root_dir.is_dir():
            continue
        rid = root_dir.name
        if args.root_id and rid != args.root_id:
            continue

        distilled_root = DISTILLED_BY_ROOT / rid
        closure_path = distilled_root / SOURCE_CLOSURE_FILE

        if closure_path.is_file():
            roots_using_closure.append(rid)
            try:
                raw = json.loads(closure_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as e:
                print(f"Invalid {closure_path}: {e}", file=sys.stderr)
                return 1
            if not isinstance(raw, dict):
                print(
                    f"{closure_path} must be a JSON object mapping rules relative paths to "
                    f"distilled path(s)",
                    file=sys.stderr,
                )
                return 1

            touched_distilled: set[Path] = set()
            distilled_base = distilled_root.resolve()

            for md in sorted(root_dir.rglob("*.md")):
                if md.name == "README.md":
                    skipped_readme += 1
                    continue
                try:
                    rel = md.relative_to(root_dir)
                except ValueError:
                    continue
                rel_posix = rel.as_posix()
                if is_excluded(rel_posix, exclude_prefixes):
                    skipped_excluded += 1
                    continue

                checked += 1
                entry = raw.get(rel_posix)
                if entry is None:
                    missing.append(
                        {
                            "root_id": rid,
                            "rules_relative": rel_posix,
                            "expected_distilled": f"(add key to {SOURCE_CLOSURE_FILE})",
                        }
                    )
                    continue
                try:
                    targets = normalize_closure_value(entry)
                except ValueError as e:
                    print(f"{closure_path} key {rel_posix!r}: {e}", file=sys.stderr)
                    return 1

                existing_outputs: list[Path] = []
                for t in targets:
                    out_path = (distilled_root / t).resolve()
                    try:
                        out_path.relative_to(distilled_base)
                    except ValueError:
                        print(
                            f"{closure_path}: path {t!r} escapes distilled root",
                            file=sys.stderr,
                        )
                        return 1
                    if out_path.is_file():
                        existing_outputs.append(out_path)
                        touched_distilled.add(out_path)
                    else:
                        missing.append(
                            {
                                "root_id": rid,
                                "rules_relative": rel_posix,
                                "expected_distilled": str(
                                    (distilled_root / t).relative_to(REPO_ROOT)
                                ),
                            }
                        )

                if existing_outputs and all(looks_like_pass_stub(p) for p in existing_outputs):
                    rules_with_only_pass_distill += 1

            for p in sorted(touched_distilled):
                if looks_like_pass_stub(p):
                    pass_stubs += 1
                else:
                    full_files += 1

        else:
            for md in sorted(root_dir.rglob("*.md")):
                if md.name == "README.md":
                    skipped_readme += 1
                    continue
                try:
                    rel = md.relative_to(root_dir)
                except ValueError:
                    continue
                rel_posix = rel.as_posix()
                if is_excluded(rel_posix, exclude_prefixes):
                    skipped_excluded += 1
                    continue

                checked += 1
                out_path = distilled_root / rel
                if not out_path.is_file():
                    missing.append(
                        {
                            "root_id": rid,
                            "rules_relative": rel_posix,
                            "expected_distilled": str(out_path.relative_to(REPO_ROOT)),
                        }
                    )
                else:
                    if looks_like_pass_stub(out_path):
                        pass_stubs += 1
                        rules_with_only_pass_distill += 1
                    else:
                        full_files += 1

    max_ratio = args.fail_if_pass_stub_ratio_above
    if max_ratio is not None and not (0.0 < max_ratio <= 1.0):
        print("--fail-if-pass-stub-ratio-above must be in (0, 1]", file=sys.stderr)
        return 1

    ratio = rules_only_pass_ratio(rules_with_only_pass_distill, checked)
    strict_violations = evaluate_strict_violations(
        checked=checked,
        full_files=full_files,
        missing_count=len(missing),
        rules_with_only_pass=rules_with_only_pass_distill,
        fail_if_all_pass_stubs=args.fail_if_all_pass_stubs,
        fail_if_any_pass_stub=args.fail_if_any_pass_stub,
        fail_if_pass_stub_ratio_above=max_ratio,
        ratio=ratio,
    )

    summary = {
        "repo_root": str(REPO_ROOT),
        "rules_by_root": str(RULES_BY_ROOT),
        "checked_rules_files": checked,
        "missing_count": len(missing),
        "skipped_readme": skipped_readme,
        "skipped_excluded": skipped_excluded,
        "rules_leaves_only_pass_stub": rules_with_only_pass_distill,
        "rules_only_pass_ratio": round(ratio, 6) if checked else None,
        "pass_stub_ratio": round(ratio, 6) if checked else None,
        "unique_distilled_pass_files": pass_stubs,
        "unique_distilled_full_files": full_files,
        "distilled_full_heuristic": full_files,
        "distilled_pass_stub_heuristic": pass_stubs,
        "roots_using_source_closure_file": roots_using_closure,
        "strict_violations": strict_violations,
        "exclude_prefixes": exclude_prefixes,
        "missing": missing,
    }

    if not json_only:
        closure_note = (
            f" source_closure={','.join(roots_using_closure)}" if roots_using_closure else ""
        )
        print(
            f"Coverage check: checked={checked} missing={len(missing)} "
            f"rules_only_pass={rules_with_only_pass_distill} "
            f"unique_distilled_pass={pass_stubs} unique_distilled_full={full_files}"
            f"{closure_note} "
            f"excluded={skipped_excluded} readme_skipped={skipped_readme}"
        )
        if rules_with_only_pass_distill > 0 and not args.quiet_pass_note:
            print(
                "Note: rules_only_pass = rules leaves covered only by Pass-distilled files "
                "(## 非业务判定（Cursor）). unique_distilled_* counts distinct files under curated "
                "(merges map many rules sources to one file). "
                "See domain-knowledge/distill-quality-bar.md.",
                file=sys.stderr,
            )
        if exclude_prefixes:
            print(f"Active exclude prefixes ({len(exclude_prefixes)}): {exclude_prefixes!r}")
        for item in missing[:200]:
            print(f"  MISSING  {item['root_id']}/{item['rules_relative']}")
            print(f"           expected: {item['expected_distilled']}")
        if len(missing) > 200:
            print(f"  ... and {len(missing) - 200} more")
        if args.json:
            print("--- json ---")
            print(json.dumps(summary, ensure_ascii=False, indent=2))

    if json_only:
        print(json.dumps(summary, ensure_ascii=False, indent=2))

    if strict_violations:
        for msg in strict_violations:
            print(f"Coverage strict check: {msg}", file=sys.stderr)
        if not args.warn_only:
            return 1
    if missing and not args.warn_only:
        return 1
    return 0
def looks_like_pass_stub(distilled: Path) -> bool:
    return looks_like_pass_stub_file(distilled, PASS_HEADINGS)




if __name__ == "__main__":
    sys.exit(main())
