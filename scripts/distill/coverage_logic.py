"""Pure helpers for distill coverage gate (testable without disk I/O)."""

from __future__ import annotations

from pathlib import Path
from typing import Collection


def looks_like_pass_stub_text(head: str, pass_headings: Collection[str]) -> bool:
    return any(marker in head for marker in pass_headings)


def looks_like_pass_stub_file(
    distilled: Path,
    pass_headings: Collection[str],
    *,
    head_bytes: int = 8000,
) -> bool:
    if not distilled.is_file():
        return False
    try:
        head = distilled.read_text(encoding="utf-8", errors="replace")[:head_bytes]
    except OSError:
        return False
    return looks_like_pass_stub_text(head, pass_headings)


def normalize_closure_value(val: object) -> list[str]:
    """Turn JSON value into a non-empty list of POSIX relative paths."""
    if isinstance(val, str):
        if not val.strip():
            raise ValueError("empty path string in source closure")
        return [val.replace("\\", "/").strip()]
    if isinstance(val, list):
        out: list[str] = []
        for item in val:
            if not isinstance(item, str) or not item.strip():
                raise ValueError("closure list entries must be non-empty strings")
            out.append(item.replace("\\", "/").strip())
        if not out:
            raise ValueError("empty target list in source closure")
        return out
    raise ValueError("closure target must be string or list of strings")


def rules_only_pass_ratio(rules_with_only_pass: int, checked: int) -> float:
    return (rules_with_only_pass / checked) if checked else 0.0


def evaluate_strict_violations(
    *,
    checked: int,
    full_files: int,
    missing_count: int,
    rules_with_only_pass: int,
    fail_if_all_pass_stubs: bool,
    fail_if_any_pass_stub: bool,
    fail_if_pass_stub_ratio_above: float | None,
    ratio: float,
) -> list[str]:
    violations: list[str] = []

    if (
        fail_if_all_pass_stubs
        and checked > 0
        and full_files == 0
        and not missing_count
    ):
        violations.append(
            "all distilled files are Pass stubs (no non-Pass curated); "
            "run Cursor RUNBOOK S4–S5 for domain drafts — path closure alone is not enough"
        )

    if fail_if_pass_stub_ratio_above is not None:
        max_ratio = fail_if_pass_stub_ratio_above
        if checked > 0 and not missing_count and ratio > max_ratio:
            violations.append(
                f"rules_only_pass_ratio={ratio:.4f} > {max_ratio} "
                f"({rules_with_only_pass}/{checked} rules leaves); complete RUNBOOK S4–S5 where needed"
            )

    if (
        fail_if_any_pass_stub
        and checked > 0
        and rules_with_only_pass > 0
        and not missing_count
    ):
        violations.append(
            f"{rules_with_only_pass} rules leaf/leaves still covered only by Pass stubs — "
            "full-tree CI requires non-Pass coverage per leaf (see distill-quality-bar.md)"
        )

    return violations
