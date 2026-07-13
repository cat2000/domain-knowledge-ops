#!/usr/bin/env python3
"""
.cursor layout: contracts/ (cross-skill docs), skills/ (+ optional _shared support),
attachment validators live under scripts/jira/attachments/.

Run from repo root:
  python3 -m unittest tests.test_skills_layout -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CURSOR = REPO / ".cursor"
SKILLS = CURSOR / "skills"
CONTRACTS_DIR = CURSOR / "contracts"
TEAM_SHARE_DIR = REPO / "docs/team-share"
JIRA_ATTACHMENTS_DIR = REPO / "scripts/jira/attachments"

CONTRACT_FILES = (
    "domain-knowledge-pipeline-contract.md",
    "jira-issue-domain-knowledge-context.md",
)

SKILL_SUBDIRS = (
    "setup-domain-ops",
    "generate-knowledge-from-wiki",
    "distill-domain-knowledge",
    "add-knowledge-from-jira",
    "requirement-risk",
    "ticket-splitter",
)

# Non-skill support dirs allowed under skills/
SKILL_SUPPORT_DIRS = frozenset({"_shared"})

JIRA_ATTACHMENT_SCRIPTS = (
    "fetch_jira_attachments.py",
    "validate_requirement_risk_report.py",
    "validate_ticket_split.py",
)

LEGACY_SKILL_SUBDIRS = ("share", "contracts", "team-share", "jira-attachments")

LEGACY_PATH_PATTERNS = (
    re.compile(r"\.cursor/skills/share/"),
    re.compile(r"\.cursor/skills/contracts/"),
    re.compile(r"\.cursor/skills/team-share/"),
    re.compile(r"\.cursor/skills/jira-attachments/"),
    re.compile(r"docs/team-share/"),
)


class TestSkillsLayout(unittest.TestCase):
    def test_contracts_dir_has_canonical_docs(self) -> None:
        self.assertTrue(CONTRACTS_DIR.is_dir(), CONTRACTS_DIR)
        for name in CONTRACT_FILES:
            with self.subTest(name=name):
                self.assertTrue((CONTRACTS_DIR / name).is_file(), name)

    def test_team_share_removed(self) -> None:
        self.assertFalse(TEAM_SHARE_DIR.exists(), TEAM_SHARE_DIR)

    def test_jira_attachment_scripts_in_scripts_tree(self) -> None:
        self.assertTrue(JIRA_ATTACHMENTS_DIR.is_dir(), JIRA_ATTACHMENTS_DIR)
        for name in JIRA_ATTACHMENT_SCRIPTS:
            with self.subTest(name=name):
                self.assertTrue((JIRA_ATTACHMENTS_DIR / name).is_file(), name)

    def test_skills_only_has_skill_and_support_subdirs(self) -> None:
        self.assertTrue(SKILLS.is_dir(), SKILLS)
        children = {p.name for p in SKILLS.iterdir() if p.is_dir()}
        self.assertTrue(set(SKILL_SUBDIRS).issubset(children), children)
        extras = children - set(SKILL_SUBDIRS) - SKILL_SUPPORT_DIRS
        self.assertEqual(extras, set(), f"unexpected skill dirs: {extras}")
        for name in SKILL_SUBDIRS:
            with self.subTest(name=name):
                self.assertTrue((SKILLS / name / "SKILL.md").is_file(), name)

    def test_legacy_skill_subdirs_removed(self) -> None:
        for name in LEGACY_SKILL_SUBDIRS:
            with self.subTest(name=name):
                self.assertFalse((SKILLS / name).exists(), name)

    def test_rules_reference_attachment_script_path(self) -> None:
        for rel in ("requirement_risk.md", "ticket_system.md"):
            body = (CURSOR / "rules" / rel).read_text(encoding="utf-8")
            self.assertIn("scripts/jira/attachments/fetch_jira_attachments.py", body, rel)

    def test_no_legacy_paths_in_active_tree(self) -> None:
        skip = {"archive", "__pycache__", ".venv", "node_modules", "agent-transcripts"}
        for path in REPO.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix not in {".md", ".py", ".mdc", ".html", ".json"}:
                continue
            if any(p in skip for p in path.parts):
                continue
            if path.name == "test_skills_layout.py":
                continue
            body = path.read_text(encoding="utf-8", errors="replace")
            for pat in LEGACY_PATH_PATTERNS:
                m = pat.search(body)
                self.assertIsNone(
                    m,
                    f"{path.relative_to(REPO)}: legacy path {pat.pattern}",
                )


if __name__ == "__main__":
    unittest.main()
