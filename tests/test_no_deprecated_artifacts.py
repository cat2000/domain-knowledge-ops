#!/usr/bin/env python3
"""
No deprecated artifacts in active scripts.

Domain-knowledge doc layout: tests.test_domain_knowledge_docs_layout.

Run from repo root:
  python3 -m unittest tests.test_no_deprecated_artifacts -v
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
from tests.domain_knowledge_contracts import (
    FORBIDDEN_JIRA_IMPORT_PREFIXES,
    LEGACY_DOMAIN_KNOWLEDGE_DIRS,
    LEGACY_SCRIPT_FILES,
    LEGACY_SCRIPT_FILES_EXTRA,
    REMOVED_SCRIPT_COMPAT_DIRS,
)

FORBIDDEN_IN_ACTIVE_PY = (
    "Compat shim",
    "Compat CLI",
    "Compat import",
    "Deprecated",
    "DEPRECATED",
    "--no-resolve-canonical-root",
    "load_认真稿_themes",
    "routing_pending_kb_outline",
    "generate_domain_knowledge_from_page",
    "LEGACY_DIR_MATERIALIZED",
    "LEGACY_DIR_CURATED",
    "LEGACY_CLOSURE_FILE",
    "LEGACY_CHECKLIST_FILE",
    "LEGACY_PASS_HEADING",
)

JIRA_PACKAGE = repo_path("scripts/jira")

SCRIPT_DOC_PATHS = (
    ".cursor/contracts/domain-knowledge-pipeline-contract.md",
    ".cursor/skills/add-knowledge-from-jira/SKILL.md",
    "scripts/README.md",
    "scripts/ARCHITECTURE.md",
)

DISTILL_GATE_SCRIPTS = (
    "distill/coverage.py",
    "distill/quality.py",
    "distill/domain_layout.py",
)


class TestNoDeprecatedArtifacts(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        ensure_scripts_on_path()

    def test_removed_scripts_absent(self) -> None:
        assert_paths_absent(self, LEGACY_SCRIPT_FILES_EXTRA, label="script")
        assert_paths_absent(self, LEGACY_SCRIPT_FILES, label="script")

    def test_compat_layer_dirs_removed(self) -> None:
        assert_paths_absent(self, REMOVED_SCRIPT_COMPAT_DIRS, label="dir")
        assert_paths_absent(self, LEGACY_DOMAIN_KNOWLEDGE_DIRS, label="dir")

    def test_jira_package_does_not_import_wiki(self) -> None:
        skip_dirs = {"archive", "__pycache__", ".venv"}
        for path in JIRA_PACKAGE.rglob("*.py"):
            if any(part in skip_dirs for part in path.parts):
                continue
            source = path.read_text(encoding="utf-8")
            rel = path.relative_to(repo_path("."))
            for prefix in FORBIDDEN_JIRA_IMPORT_PREFIXES:
                self.assertNotIn(prefix, source, f"{rel} must not {prefix}")

    def test_active_python_has_no_deprecated_markers(self) -> None:
        skip_dirs = {"archive", "__pycache__", ".venv"}
        for path in repo_path("scripts").rglob("*.py"):
            if any(part in skip_dirs for part in path.parts):
                continue
            source = path.read_text(encoding="utf-8")
            rel = path.relative_to(repo_path("."))
            for token in FORBIDDEN_IN_ACTIVE_PY:
                self.assertNotIn(token, source, f"{rel} must not contain {token!r}")

    def test_script_docs_no_compat_cli_paths(self) -> None:
        for rel in SCRIPT_DOC_PATHS:
            body = read_repo_text(rel)
            with self.subTest(doc=rel):
                self.assertNotIn("/cli/", body)
                self.assertNotIn("/imports/", body)
                self.assertNotIn("run_bc_jira_sprint_fetch", body)

    def test_domain_check_delegates_to_distill_modules(self) -> None:
        domain_check = read_repo_text("scripts/domain_check.py")
        self.assertIn("distill/coverage.py", domain_check)
        self.assertNotIn("distill/cli/", domain_check)

    def test_facet_classify_module_resolves(self) -> None:
        from wiki.sync.env import FACET_CLASSIFY_MODULE

        self.assertTrue(FACET_CLASSIFY_MODULE.is_file())
        self.assertIn("facet_classify.py", str(FACET_CLASSIFY_MODULE))

    def test_distill_gate_scripts_accept_help(self) -> None:
        for script in DISTILL_GATE_SCRIPTS:
            proc = run_script_help(f"scripts/{script}")
            with self.subTest(script=script):
                self.assertEqual(proc.returncode, 0, proc.stderr[:300])


if __name__ == "__main__":
    unittest.main()
