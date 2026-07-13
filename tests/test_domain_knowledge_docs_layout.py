#!/usr/bin/env python3
"""
TDD contract: domain-knowledge doc layout (files, git index, canonical doc names).

Run from repo root:
  python3 -m unittest tests.test_domain_knowledge_docs_layout -v
"""

from __future__ import annotations

import json
import unittest

from tests.contract_support import (
    assert_docs_exclude_tokens,
    assert_git_untracked,
    assert_paths_absent,
    assert_paths_are_files,
    ensure_scripts_on_path,
    read_repo_text,
    repo_path,
)
from tests.domain_knowledge_contracts import (
    DOC_PATHS_FOR_LEGACY_SCAN,
    FORBIDDEN_DOC_TOKENS,
    GIT_UNTRACKED_LEGACY_PATHS,
    LEGACY_DOMAIN_KNOWLEDGE_DIRS,
    LEGACY_DOMAIN_KNOWLEDGE_DOCS,
    LEGACY_SCRIPT_FILES,
    LEGACY_WIKI_SKILL_DOC_PATHS,
    REQUIRED_DOMAIN_KNOWLEDGE_DOCS,
)

DISTILL_GATE_SCRIPTS = ("distill/coverage.py", "distill/domain_layout.py")


class TestDomainKnowledgeDocsLayout(unittest.TestCase):
    def test_no_legacy_domain_knowledge_artifacts_on_disk(self) -> None:
        assert_paths_absent(self, LEGACY_DOMAIN_KNOWLEDGE_DOCS)
        assert_paths_absent(self, LEGACY_DOMAIN_KNOWLEDGE_DIRS, label="dir")
        assert_paths_absent(self, LEGACY_SCRIPT_FILES, label="script")
        assert_paths_absent(self, LEGACY_WIKI_SKILL_DOC_PATHS, label="skill_doc")

    def test_required_domain_knowledge_docs_exist(self) -> None:
        assert_paths_are_files(self, REQUIRED_DOMAIN_KNOWLEDGE_DOCS)

    def test_legacy_domain_knowledge_paths_not_tracked_in_git(self) -> None:
        assert_git_untracked(self, GIT_UNTRACKED_LEGACY_PATHS)

    def test_active_docs_use_canonical_names_only(self) -> None:
        assert_docs_exclude_tokens(
            self, DOC_PATHS_FOR_LEGACY_SCAN, FORBIDDEN_DOC_TOKENS
        )

    def test_readme_links_jira_readme_not_legacy_pipeline(self) -> None:
        readme = read_repo_text("domain-knowledge/README.md")
        self.assertIn("jira/README.md", readme)
        self.assertNotIn("jira-pipeline", readme)

    def test_team_roots_has_no_publish_deliver_config(self) -> None:
        teams = json.loads(read_repo_text("domain-knowledge/jira/team-roots.json")).get(
            "teams", {}
        )
        for team_key, record in teams.items():
            with self.subTest(team=team_key):
                self.assertNotIn("deliver", record)

    def test_distill_gates_share_exclude_module(self) -> None:
        ensure_scripts_on_path()
        self.assertTrue(repo_path("scripts/distill/_exclude.py").is_file())
        for script in DISTILL_GATE_SCRIPTS:
            source = read_repo_text(f"scripts/{script}")
            with self.subTest(script=script):
                self.assertIn("from distill._exclude import", source)
                self.assertNotIn("def load_exclude_prefixes", source)

    def test_coverage_has_no_default_exclude_file_hook(self) -> None:
        source = read_repo_text("scripts/distill/coverage.py")
        for token in (
            "coverage-distill-exclude",
            "no-default-exclude-file",
            "DEFAULT_EXCLUDE_FILE",
        ):
            self.assertNotIn(token, source, token)


if __name__ == "__main__":
    unittest.main()
