#!/usr/bin/env python3
"""
TDD contract for Wiki S1 CLI (sync_domain_knowledge_from_confluence).

Run from repo root:
  python3 -m unittest tests.test_wiki_s1_cli_naming -v
"""

from __future__ import annotations

import unittest

from tests.contract_support import (
    assert_paths_absent,
    ensure_scripts_on_path,
    read_repo_text,
    repo_path,
    run_script_help,
)
from tests.domain_knowledge_contracts import LEGACY_WIKI_SKILL_DOC_PATHS

WIKI_SKILL_DIR = ".cursor/skills/generate-knowledge-from-wiki"
LEGACY_CLI = "generate_domain_knowledge_from_page.py"

PRIMARY_CONTRACT_DOCS = (
    f"{WIKI_SKILL_DIR}/RUNBOOK.md",
    f"{WIKI_SKILL_DIR}/SKILL.md",
    f"{WIKI_SKILL_DIR}/S1-SYNC-CLI.md",
    ".cursor/contracts/domain-knowledge-pipeline-contract.md",
    "scripts/README.md",
    "scripts/ARCHITECTURE.md",
    "domain-knowledge/README.md",
)

class TestWikiS1CliNaming(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        ensure_scripts_on_path()

    def test_wiki_cli_ssot_constants(self) -> None:
        from runtime.wiki_cli import (
            WIKI_RUNBOOK_DOC,
            WIKI_S1_CLI,
            WIKI_S1_CLI_DOC,
            WIKI_S1_LOG_PREFIX,
        )

        self.assertEqual(WIKI_S1_CLI, "sync_domain_knowledge_from_confluence.py")
        self.assertEqual(WIKI_S1_LOG_PREFIX, "sync_domain_knowledge_from_confluence")
        self.assertEqual(WIKI_S1_CLI_DOC, "S1-SYNC-CLI.md")
        self.assertEqual(WIKI_RUNBOOK_DOC, "RUNBOOK.md")

    def test_wiki_skill_has_required_docs_only(self) -> None:
        from runtime.wiki_cli import LEGACY_WIKI_SKILL_DOCS, WIKI_SKILL_EXTRA_DOCS

        skill_dir = repo_path(WIKI_SKILL_DIR)
        self.assertTrue((skill_dir / "SKILL.md").is_file())
        for name in WIKI_SKILL_EXTRA_DOCS:
            with self.subTest(doc=name):
                self.assertTrue((skill_dir / name).is_file(), name)
        for name in LEGACY_WIKI_SKILL_DOCS:
            with self.subTest(legacy=name):
                self.assertFalse((skill_dir / name).exists(), name)
        assert_paths_absent(self, LEGACY_WIKI_SKILL_DOC_PATHS, label="skill_doc")
        self.assertIn("## Appendix · Step Quick Reference", read_repo_text(f"{WIKI_SKILL_DIR}/RUNBOOK.md"))
        self.assertIn("## 附录 · 步骤速查", read_repo_text(f"{WIKI_SKILL_DIR}/RUNBOOK.zh-CN.md"))

    def test_legacy_s1_cli_shim_removed(self) -> None:
        self.assertFalse(repo_path(f"scripts/{LEGACY_CLI}").exists())

    def test_canonical_s1_cli_exists_and_prints_help(self) -> None:
        from runtime.wiki_cli import WIKI_S1_CLI

        cli = repo_path(f"scripts/{WIKI_S1_CLI}")
        self.assertTrue(cli.is_file())
        proc = run_script_help(f"scripts/{WIKI_S1_CLI}")
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
        self.assertIn("Confluence", proc.stdout)

    def test_s1_sync_cli_doc_renamed_from_reference(self) -> None:
        from runtime.wiki_cli import WIKI_S1_CLI_DOC

        self.assertTrue(repo_path(f"{WIKI_SKILL_DIR}/{WIKI_S1_CLI_DOC}").is_file())
        self.assertFalse(repo_path(f"{WIKI_SKILL_DIR}/reference.md").exists())

    def test_runbook_and_skill_link_s1_sync_cli_doc(self) -> None:
        from runtime.wiki_cli import WIKI_S1_CLI_DOC

        for rel in (f"{WIKI_SKILL_DIR}/SKILL.md", f"{WIKI_SKILL_DIR}/RUNBOOK.md"):
            self.assertIn(WIKI_S1_CLI_DOC, read_repo_text(rel), rel)

    def test_primary_contracts_reference_canonical_s1_cli_only(self) -> None:
        from runtime.wiki_cli import WIKI_S1_CLI

        for rel in PRIMARY_CONTRACT_DOCS:
            body = read_repo_text(rel)
            with self.subTest(doc=rel):
                self.assertIn(WIKI_S1_CLI, body)
                self.assertNotIn(LEGACY_CLI, body)

    def test_pipeline_logs_use_canonical_prefix(self) -> None:
        from runtime.wiki_cli import WIKI_S1_LOG_PREFIX

        pipeline_run = read_repo_text("scripts/wiki/sync/pipeline_run.py")
        self.assertIn(WIKI_S1_LOG_PREFIX, pipeline_run)
        self.assertNotIn(LEGACY_CLI.replace(".py", ":"), pipeline_run)


if __name__ == "__main__":
    unittest.main()
