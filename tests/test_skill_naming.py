#!/usr/bin/env python3
"""
TDD contract for Cursor Skill rename:
  generate-knowledge → generate-knowledge-from-wiki
  jira-knowledge → add-knowledge-from-jira

Run from repo root:
  python3 -m unittest tests.test_skill_naming -v
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SKILLS = REPO / ".cursor/skills"

PRIMARY_CONTRACTS = [
    REPO / ".cursor/skills/README.md",
    REPO / ".cursor/contracts/domain-knowledge-pipeline-contract.md",
    REPO / ".cursor/skills/distill-domain-knowledge/SKILL.md",
    REPO / ".cursor/skills/requirement-risk/SKILL.md",
    REPO / ".cursor/skills/ticket-splitter/SKILL.md",
    REPO / "scripts/wiki/sync/handoff.py",
    REPO / "domain-knowledge/README.md",
    REPO / "TEAM_KNOWLEDGE_BASE.md",
]

LEGACY_DIR_PATTERNS = (
    re.compile(r"\.cursor/skills/generate-knowledge/"),
    re.compile(r"\.cursor/skills/jira-knowledge/"),
    re.compile(r"@generate-knowledge(?!-from-wiki)"),
    re.compile(r"@jira-knowledge\b"),
    re.compile(r"name:\s+generate-knowledge\s*$", re.M),
    re.compile(r"name:\s+jira-knowledge\s*$", re.M),
    re.compile(r'"pipeline":\s+"generate-knowledge"'),
)


def _scripts_on_path() -> None:
    s = str(REPO / "scripts")
    if s not in sys.path:
        sys.path.insert(0, s)


class TestSkillNaming(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _scripts_on_path()

    def test_ssot_constants(self) -> None:
        from runtime.skill_names import (
            JIRA_SKILL,
            LEGACY_JIRA_SKILL,
            LEGACY_WIKI_SKILL,
            WIKI_SKILL,
        )

        self.assertEqual(WIKI_SKILL, "generate-knowledge-from-wiki")
        self.assertEqual(JIRA_SKILL, "add-knowledge-from-jira")
        self.assertEqual(LEGACY_WIKI_SKILL, "generate-knowledge")
        self.assertEqual(LEGACY_JIRA_SKILL, "jira-knowledge")

    def test_skill_dirs_renamed(self) -> None:
        from runtime.skill_names import JIRA_SKILL, LEGACY_JIRA_SKILL, LEGACY_WIKI_SKILL, WIKI_SKILL

        self.assertTrue((SKILLS / WIKI_SKILL / "SKILL.md").is_file())
        self.assertTrue((SKILLS / WIKI_SKILL / "RUNBOOK.md").is_file())
        self.assertTrue((SKILLS / JIRA_SKILL / "SKILL.md").is_file())
        self.assertFalse((SKILLS / LEGACY_WIKI_SKILL).exists())
        self.assertFalse((SKILLS / LEGACY_JIRA_SKILL).exists())

    def test_wiki_skill_frontmatter(self) -> None:
        from runtime.skill_names import WIKI_SKILL

        text = (SKILLS / WIKI_SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn(f"name: {WIKI_SKILL}", text)
        self.assertIn("S1", text)
        self.assertIn("S5", text)

    def test_jira_skill_frontmatter(self) -> None:
        from runtime.skill_names import JIRA_SKILL

        text = (SKILLS / JIRA_SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn(f"name: {JIRA_SKILL}", text)

    def test_primary_contracts_use_new_skills(self) -> None:
        from runtime.skill_names import JIRA_SKILL, WIKI_SKILL

        for path in PRIMARY_CONTRACTS:
            body = path.read_text(encoding="utf-8")
            if path.name == "handoff.py":
                self.assertIn("WIKI_SKILL", body, path.name)
            else:
                self.assertIn(WIKI_SKILL, body, path.name)
            if path.name in ("domain-knowledge-pipeline-contract.md", "README.md", "TEAM_KNOWLEDGE_BASE.md"):
                self.assertIn(JIRA_SKILL, body, path.name)

    def test_no_legacy_skill_references_in_active_tree(self) -> None:
        skip = {"archive", "__pycache__", ".venv", "node_modules"}
        for path in REPO.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix not in {".md", ".py", ".mdc", ".html", ".json", ".yml", ".yaml"}:
                continue
            if any(p in skip for p in path.parts):
                continue
            if "agent-transcripts" in path.parts:
                continue
            if path.name == "test_skill_naming.py":
                continue
            body = path.read_text(encoding="utf-8", errors="replace")
            for pat in LEGACY_DIR_PATTERNS:
                m = pat.search(body)
                self.assertIsNone(
                    m,
                    f"{path.relative_to(REPO)}: legacy skill pattern {pat.pattern}",
                )

    def test_handoff_pipeline_field(self) -> None:
        from runtime.skill_names import WIKI_SKILL

        text = (REPO / "scripts/wiki/sync/handoff.py").read_text(encoding="utf-8")
        self.assertIn("from runtime.skill_names import WIKI_SKILL", text)
        self.assertIn('"pipeline": WIKI_SKILL', text)
        self.assertIn(f'f"{{WIKI_SKILL}}/RUNBOOK.md', text)
        self.assertEqual(WIKI_SKILL, "generate-knowledge-from-wiki")


if __name__ == "__main__":
    unittest.main()
