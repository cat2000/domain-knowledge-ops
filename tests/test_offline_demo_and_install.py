#!/usr/bin/env python3
"""Offline demo fixture + skills/ install symlinks must ship."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FIXTURE = REPO / "domain-knowledge/fixtures/offline-demo"
SKILLS_TOP = REPO / "skills"
CURSOR_SKILLS = REPO / ".cursor/skills"


class TestOfflineDemoFixture(unittest.TestCase):
    def test_fixture_ticket_and_brief_exist(self) -> None:
        self.assertTrue((FIXTURE / "README.md").is_file())
        self.assertTrue((FIXTURE / "jira/DEMO-1.md").is_file())
        self.assertTrue((FIXTURE / "jira/DEMO-1.attribution.yaml").is_file())
        brief = (
            FIXTURE
            / "curated/by-root/100001/_deliver/ordering/ordering-domain-brief.md"
        )
        self.assertTrue(brief.is_file(), brief)
        body = brief.read_text(encoding="utf-8")
        self.assertIn("Quote Version", body)
        self.assertIn("Confirmed rule", body)

        zh_sibling = (
            FIXTURE
            / "curated/by-root/100001/_deliver/ordering/ordering-领域知识定稿.md"
        )
        self.assertTrue(zh_sibling.is_file(), zh_sibling)
        zh_body = zh_sibling.read_text(encoding="utf-8")
        self.assertIn("报价版本", zh_body)
        self.assertIn("已确认规则", zh_body)
        self.assertIn("ordering-domain-brief.md", zh_body)

    def test_saas_billing_fixture_exists(self) -> None:
        billing = REPO / "domain-knowledge/fixtures/saas-billing"
        self.assertTrue((billing / "jira/DEMO-BILL-1.md").is_file())
        brief = (
            billing
            / "curated/by-root/100001/_deliver/billing/billing-domain-brief.md"
        )
        self.assertTrue(brief.is_file(), brief)
        body = brief.read_text(encoding="utf-8")
        self.assertIn("Proration", body)
        self.assertIn("Confirmed rule", body)

    def test_wiki_skill_is_thin_and_iron_laws_split(self) -> None:
        skill = CURSOR_SKILLS / "generate-knowledge-from-wiki/SKILL.md"
        iron = CURSOR_SKILLS / "generate-knowledge-from-wiki/references/iron-laws.md"
        self.assertTrue(skill.is_file())
        self.assertTrue(iron.is_file())
        lines = skill.read_text(encoding="utf-8").splitlines()
        self.assertLessEqual(len(lines), 120, f"SKILL.md too long: {len(lines)}")
        self.assertIn("references/iron-laws.md", skill.read_text(encoding="utf-8"))
        self.assertIn("Strategy-first", iron.read_text(encoding="utf-8"))

    def test_top_level_skills_symlinks(self) -> None:
        self.assertTrue((REPO / "INSTALL.md").is_file())
        for name in (
            "requirement-risk",
            "ticket-splitter",
            "ticket-test-design",
            "setup-domain-ops",
            "generate-knowledge-from-wiki",
        ):
            link = SKILLS_TOP / name
            self.assertTrue(link.exists(), link)
            self.assertTrue((link / "SKILL.md").is_file(), name)

    def test_walkthrough_and_first_run_exist(self) -> None:
        self.assertTrue((REPO / "WALKTHROUGH.md").is_file())
        self.assertTrue((FIXTURE / "INDUSTRY.md").is_file())
        first = CURSOR_SKILLS / "generate-knowledge-from-wiki/FIRST-RUN.md"
        self.assertTrue(first.is_file())
        skill = (CURSOR_SKILLS / "generate-knowledge-from-wiki/SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("FIRST-RUN.md", skill)
        runbook = (CURSOR_SKILLS / "generate-knowledge-from-wiki/RUNBOOK.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Do not read this file end-to-end", runbook)

    def test_verify_skills_pack_script(self) -> None:
        import subprocess
        import sys

        proc = subprocess.run(
            [sys.executable, str(REPO / "scripts/verify_skills_pack.py")],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)


if __name__ == "__main__":
    unittest.main()
