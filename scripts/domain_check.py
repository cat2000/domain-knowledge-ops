#!/usr/bin/env python3
"""
Unified KB gate facade (no new checks — delegates to existing scripts).

  python3 scripts/domain_check.py distill --root-id <ROOT_ID>
  python3 scripts/domain_check.py jira --team <team-key> --full-raw
  python3 scripts/domain_check.py all --team <team-key>
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

_SCRIPTS = next(p for p in Path(__file__).resolve().parents if (p / "_install.py").is_file())
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
import _install

_install.bootstrap(__file__)
from _bootstrap import REPO_ROOT, SCRIPTS_DIR

def main() -> int:
    parser = argparse.ArgumentParser(description="KB pipeline gate facade")
    sub = parser.add_subparsers(dest="command", required=True)

    for name in ("distill", "jira", "all"):
        p = sub.add_parser(name, help=f"Run {name} gates")
        p.add_argument("--root-id", help="Confluence storage root (distill / all)")
        from teams.registry import add_team_argument

        add_team_argument(p, use_default=False)
        p.add_argument("--full-raw", action="store_true", help="Jira: --full-raw")
        p.add_argument(
            "--warn-only",
            action="store_true",
            help="Distill checks: forward --warn-only to scripts/distill/*.py",
        )
        p.add_argument(
            "passthrough",
            nargs=argparse.REMAINDER,
            help="Extra args forwarded to underlying check scripts",
        )

    args = parser.parse_args()
    passthrough = [x for x in (args.passthrough or []) if x != "--"]

    jira_extra: list[str] = list(passthrough)
    if args.full_raw:
        jira_extra.append("--full-raw")

    distill_extra: list[str] = list(passthrough)
    if getattr(args, "warn_only", False):
        distill_extra.append("--warn-only")

    if args.command == "distill":
        root_id = _resolve_root_id(args.team, args.root_id)
        return _distill_checks(root_id, distill_extra)

    if args.command == "jira":
        return _jira_checks(args.team or "", jira_extra)

    # all
    root_id = _resolve_root_id(args.team, args.root_id)
    exit_code = _distill_checks(root_id, distill_extra)
    if args.team:
        jira_exit_code = _jira_checks(args.team, jira_extra)
        if jira_exit_code != 0:
            exit_code = jira_exit_code
    else:
        from teams.registry import configured_team_keys

        keys = configured_team_keys()
        hint = "|".join(keys) if keys else "<team-key>"
        print(
            f"domain_check all: skipped Jira gates (pass --team {hint} to include them)",
            file=sys.stderr,
        )
    return exit_code
def _distill_checks(root_id: str, extra: list[str]) -> int:
    layers: list[tuple[str, list[str]]] = [
        (
            "S2 认域层",
            [
                "distill/coverage.py",
            ],
        ),
        (
            "S3 结构层",
            [
                "distill/proposition_quality.py",
                "distill/s3_quality.py",
                "distill/decision_atom_quality.py",
                "distill/conflict_ledger_quality.py",
            ],
        ),
        (
            "S4/S5 模型与语义层",
            [
                "distill/domain_model_quality.py",
                "distill/s5_work_draft_quality.py",
                "distill/quality.py",
                "distill/domain_layout.py",
            ],
        ),
        (
            "S6 承诺层",
            [
                "distill/s6_reader_quality.py",
            ],
        ),
    ]
    exit_code = 0
    layer_failures: list[tuple[str, int, int]] = []
    for layer_name, scripts in layers:
        print(f"[domain_check] {layer_name}: start", file=sys.stderr)
        failed = 0
        for name in scripts:
            prev_s3_report = None
            if name == "distill/s3_quality.py":
                prev_s3_report = _load_s3_quality_report(root_id)
            code = _run(name, ["--root-id", root_id, *extra])
            if code != 0:
                failed += 1
                exit_code = code
            if name == "distill/s3_quality.py":
                curr_s3_report = _load_s3_quality_report(root_id)
                _print_s3_quality_trend(prev_s3_report, curr_s3_report)
        total = len(scripts)
        layer_failures.append((layer_name, failed, total))
        print(f"[domain_check] {layer_name}: {'PASS' if failed == 0 else 'FAIL'} ({total - failed}/{total})", file=sys.stderr)
    print("[domain_check] Distill layered summary:", file=sys.stderr)
    for layer_name, failed, total in layer_failures:
        print(f"  - {layer_name}: {'PASS' if failed == 0 else 'FAIL'} ({total - failed}/{total})", file=sys.stderr)
    return exit_code


def _jira_checks(team: str, extra: list[str]) -> int:
    if not team:
        raise SystemExit("domain_check jira/all: --team is required")
    return _run("jira/steps/check_pipeline.py", ["--team", team, *extra])


def _resolve_root_id(team: str | None, root_id: str | None) -> str:
    if root_id:
        return str(root_id).strip()
    if not team:
        raise SystemExit("domain_check: provide --root-id or --team (for default root_id)")
    from teams.registry import resolve_team

    _, cfg = resolve_team(team)
    rid = str(cfg.get("root_id") or "").strip()
    if not rid:
        raise SystemExit(f"domain_check: no root_id for team {team!r}")
    return rid


def _run(script: str, args: list[str]) -> int:
    cmd = [_py(), str(SCRIPTS_DIR / script), *args]
    print("+", " ".join(cmd), file=sys.stderr)
    return subprocess.run(cmd, cwd=str(REPO_ROOT)).returncode


def _py() -> str:
    return sys.executable


def _load_s3_quality_report(root_id: str) -> dict[str, object] | None:
    path = REPO_ROOT / "domain-knowledge" / "curated" / "by-root" / str(root_id).strip() / "S3_QUALITY_REPORT.json"
    if not path.is_file():
        return None
    try:
        return dict(json.loads(path.read_text(encoding="utf-8")))
    except Exception:
        return None


def _print_s3_quality_trend(prev_report: dict[str, object] | None, curr_report: dict[str, object] | None) -> None:
    if curr_report is None:
        print("[domain_check] S3 趋势: 当前报告缺失，跳过对比", file=sys.stderr)
        return
    if prev_report is None:
        print("[domain_check] S3 趋势: 首次生成报告，后续运行将显示增量", file=sys.stderr)
        return

    prev_slugs = _slug_metrics_map(prev_report)
    curr_slugs = _slug_metrics_map(curr_report)
    common = sorted(set(prev_slugs) & set(curr_slugs))
    if not common:
        print("[domain_check] S3 趋势: 无共同 slug，跳过对比", file=sys.stderr)
        return

    metrics = [
        ("contract_coverage", True),
        ("high_confidence_rate", True),
        ("unknown_rate", False),
        ("branch_integrity", True),
    ]
    mean_parts: list[str] = []
    regressions: list[str] = []
    for key, higher_is_better in metrics:
        deltas: list[tuple[str, float]] = []
        for slug in common:
            prev_v = float(prev_slugs[slug].get(key) or 0.0)
            curr_v = float(curr_slugs[slug].get(key) or 0.0)
            delta = curr_v - prev_v
            deltas.append((slug, delta))
            if higher_is_better:
                degraded = delta < -0.01
            else:
                degraded = delta > 0.01
            if degraded:
                regressions.append(f"{slug}:{key}:{delta:+.3f}")
        mean_delta = sum(d for _, d in deltas) / len(deltas)
        sign = "+" if mean_delta >= 0 else ""
        mean_parts.append(f"{key}={sign}{mean_delta:.3f}")

    prev_issues = int(prev_report.get("issues_total") or 0)
    curr_issues = int(curr_report.get("issues_total") or 0)
    issues_delta = curr_issues - prev_issues
    issues_sign = "+" if issues_delta >= 0 else ""
    print(
        f"[domain_check] S3 趋势: common_slugs={len(common)} {', '.join(mean_parts)} issues_total={curr_issues} ({issues_sign}{issues_delta})",
        file=sys.stderr,
    )
    if regressions:
        sample = ", ".join(sorted(regressions)[:6])
        print(f"[domain_check] S3 趋势回退: {sample}", file=sys.stderr)


def _slug_metrics_map(report: dict[str, object]) -> dict[str, dict[str, object]]:
    out: dict[str, dict[str, object]] = {}
    for row in list(report.get("slug_metrics") or []):
        d = dict(row)
        slug = str(d.get("slug") or "").strip()
        if slug:
            out[slug] = d
    return out




if __name__ == "__main__":
    raise SystemExit(main())
