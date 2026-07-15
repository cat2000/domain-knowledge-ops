#!/usr/bin/env python3
"""Verify this repo is installable as an agentskills / npx-skills style pack.

Run from repo root (no network required):

  python3 scripts/verify_skills_pack.py

Exit 0 = layout OK for Cursor + top-level ``skills/`` discovery.
This is the local stand-in for “public repo validation” until a remote + CI
green check is published.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_SCRIPTS = next(p for p in Path(__file__).resolve().parents if (p / "_install.py").is_file())
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
import _install

_install.bootstrap(__file__)
from _bootstrap import REPO_ROOT

CURSOR_SKILLS = REPO_ROOT / ".cursor" / "skills"
TOP_SKILLS = REPO_ROOT / "skills"

REQUIRED = (
    "setup-domain-ops",
    "generate-knowledge-from-wiki",
    "distill-domain-knowledge",
    "add-knowledge-from-jira",
    "requirement-risk",
    "ticket-splitter",
    "ticket-test-design",
)

FM_NAME = re.compile(r"^name:\s*([^\s#]+)\s*$", re.M)
FM_DESC = re.compile(r"^description:\s*", re.M)


def _fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)


def _ok(msg: str) -> None:
    print(f"OK:   {msg}")


def verify() -> int:
    errors = 0

    if not CURSOR_SKILLS.is_dir():
        _fail(f"missing {CURSOR_SKILLS.relative_to(REPO_ROOT)}")
        return 1

    if not TOP_SKILLS.is_dir():
        _fail(f"missing {TOP_SKILLS.relative_to(REPO_ROOT)} (npx skills discovery root)")
        return 1

    for name in REQUIRED:
        cursor = CURSOR_SKILLS / name
        skill_md = cursor / "SKILL.md"
        top = TOP_SKILLS / name

        if not skill_md.is_file():
            _fail(f".cursor/skills/{name}/SKILL.md missing")
            errors += 1
            continue

        text = skill_md.read_text(encoding="utf-8")
        if not text.startswith("---"):
            _fail(f"{name}: SKILL.md missing YAML frontmatter")
            errors += 1
        else:
            m = FM_NAME.search(text)
            if not m or m.group(1) != name:
                _fail(f"{name}: frontmatter name must be `{name}` (got {m.group(1) if m else None})")
                errors += 1
            if not FM_DESC.search(text):
                _fail(f"{name}: frontmatter description missing")
                errors += 1
            else:
                _ok(f"{name}: frontmatter")

        if not top.exists():
            _fail(f"skills/{name} missing (symlink or copy for installers)")
            errors += 1
        elif top.is_symlink():
            resolved = top.resolve()
            if resolved != cursor.resolve():
                _fail(f"skills/{name} → {resolved}, expected {cursor}")
                errors += 1
            else:
                _ok(f"skills/{name} → .cursor/skills/{name}")
        elif not (top / "SKILL.md").is_file():
            _fail(f"skills/{name}/SKILL.md missing")
            errors += 1
        else:
            _ok(f"skills/{name} present")

    for rel in (
        "WALKTHROUGH.md",
        "INSTALL.md",
        "CONTRIBUTING.md",
        "docs/METHODOLOGY.md",
        "docs/BENCHMARK.md",
        "domain-knowledge/fixtures/offline-demo/README.md",
        "domain-knowledge/fixtures/offline-demo/jira/DEMO-1.md",
        "domain-knowledge/fixtures/offline-demo/curated/by-root/100001/_deliver/ordering/ordering-domain-brief.md",
        "domain-knowledge/fixtures/saas-billing/README.md",
        "domain-knowledge/fixtures/saas-billing/jira/DEMO-BILL-1.md",
        "domain-knowledge/fixtures/saas-billing/curated/by-root/100001/_deliver/billing/billing-domain-brief.md",
        ".cursor/skills/generate-knowledge-from-wiki/FIRST-RUN.md",
        ".cursor/skills/generate-knowledge-from-wiki/references/industry-axis-remount.md",
    ):
        path = REPO_ROOT / rel
        if path.is_file():
            _ok(rel)
        else:
            _fail(f"missing {rel}")
            errors += 1

    if errors:
        print(f"\n{errors} error(s). Fix before advertising npx skills install.", file=sys.stderr)
        return 1
    print("\nSkills pack layout verified (offline).")
    return 0


if __name__ == "__main__":
    raise SystemExit(verify())
