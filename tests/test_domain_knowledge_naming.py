#!/usr/bin/env python3
"""
TDD contract for domain-knowledge naming (2026-05 refactor).

Run from repo root:
  python3 -m unittest tests.test_domain_knowledge_naming -v
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"
DOMAIN_KNOWLEDGE = REPO / "domain-knowledge"

TEAM_ROOTS = ("100001",)

CONTRACT_PATHS = [
    REPO / ".cursor/skills/generate-knowledge-from-wiki/RUNBOOK.md",
    REPO / ".cursor/skills/generate-knowledge-from-wiki/SKILL.md",
    REPO / "domain-knowledge/distill-quality-bar.md",
    REPO / "scripts/wiki/sync/handoff.py",
    REPO / "scripts/distill/_paths.py",
    REPO / "scripts/distill/coverage.py",
]

FORBIDDEN_IN_CONTRACT = (
    "domain-knowledge/rules/",
    "domain-knowledge/rules-distilled/",
    "routing-pending/",
    "ACCEPTANCE_CHECKLIST.md",
    "_source_closure.json",
)

CONTRACT_EXTRA_REQUIRED: dict[str, tuple[str, ...]] = {
    "RUNBOOK.md": ("curated/", "facet-unmatched", "materialized/by-root"),
    "handoff.py": ("materialized_dir", "CURATED_BY_ROOT"),
    "distill-quality-bar.md": ("DOMAIN_MODULE_CHECKLIST",),
}

REQUIRED_IN_RUNBOOK = (
    "materialized/",
    "curated/",
    "facet-unmatched",
    "DOMAIN_MODULE_CHECKLIST",
    "_materialization_closure",
    "Recognize",
    "non-business determination",
)

REQUIRED_IN_SKILL = (
    "curated/",
    "RUNBOOK.md",
    "iron-laws.md",
    "confirm",
    "setup-domain-ops",
)


def _scripts_on_path() -> None:
    s = str(SCRIPTS)
    if s not in sys.path:
        sys.path.insert(0, s)


class TestNamingSSOT(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _scripts_on_path()

    def test_canonical_top_level_dirs_exist(self) -> None:
        from runtime.domain_knowledge_paths import (
            CURATED_BY_ROOT,
            MATERIALIZED_BY_ROOT,
            DIR_CURATED,
            DIR_MATERIALIZED,
        )

        self.assertTrue(MATERIALIZED_BY_ROOT.is_dir(), DIR_MATERIALIZED)
        self.assertTrue(CURATED_BY_ROOT.is_dir(), DIR_CURATED)
        legacy_rules = DOMAIN_KNOWLEDGE / "rules"
        legacy_distilled = DOMAIN_KNOWLEDGE / "rules-distilled"
        self.assertFalse(legacy_rules.exists(), "legacy rules/ should be renamed")
        self.assertFalse(legacy_distilled.exists(), "legacy rules-distilled/ should be renamed")

    def test_facet_classify_module(self) -> None:
        from wiki.lib import facet_classify
        from wiki.lib.facet_classify import classify, FACET_DIRS

        theme, kb = classify("Checkout payment", "wechat pay cart")
        self.assertIsInstance(theme, str)
        self.assertTrue(kb.startswith("facet-") or kb == "—")
        self.assertIn("facet-checkout", FACET_DIRS)

    def test_facet_unmatched_fallback_outline(self) -> None:
        from wiki.lib.confluence_classify_utils import facet_unmatched_kb_outline

        outline = facet_unmatched_kb_outline("Some Random Page")
        self.assertTrue(outline.startswith("facet-unmatched/"))

    def test_distill_paths_use_ssot(self) -> None:
        from distill._paths import (
            CURATED_BY_ROOT,
            MATERIALIZED_BY_ROOT,
            MATERIALIZATION_CLOSURE_FILE,
            NON_BUSINESS_HEADING,
        )
        from runtime.domain_knowledge_paths import (
            CURATED_BY_ROOT as SSOT_CURATED,
            MATERIALIZED_BY_ROOT as SSOT_MAT,
            MATERIALIZATION_CLOSURE_FILE as SSOT_CLOSURE,
            NON_BUSINESS_HEADING as SSOT_HEADING,
        )

        self.assertEqual(CURATED_BY_ROOT, SSOT_CURATED)
        self.assertEqual(MATERIALIZED_BY_ROOT, SSOT_MAT)
        self.assertEqual(MATERIALIZATION_CLOSURE_FILE, SSOT_CLOSURE)
        self.assertEqual(NON_BUSINESS_HEADING, SSOT_HEADING)

    def test_team_closure_and_checklist_canonical_names(self) -> None:
        from runtime.domain_knowledge_paths import (
            DOMAIN_MODULE_CHECKLIST_FILE,
            MATERIALIZATION_CLOSURE_FILE,
        )

        for root_id in TEAM_ROOTS:
            with self.subTest(root_id=root_id):
                base = DOMAIN_KNOWLEDGE / "curated" / "by-root" / root_id
                if not base.is_dir():
                    continue
                if not (base / MATERIALIZATION_CLOSURE_FILE).is_file():
                    continue
                self.assertTrue(
                    (base / MATERIALIZATION_CLOSURE_FILE).is_file(),
                    MATERIALIZATION_CLOSURE_FILE,
                )
                self.assertTrue(
                    (base / DOMAIN_MODULE_CHECKLIST_FILE).is_file(),
                    DOMAIN_MODULE_CHECKLIST_FILE,
                )

    def test_closure_keys_use_facet_prefixes(self) -> None:
        from runtime.domain_knowledge_paths import (
            FORBIDDEN_MATERIALIZED_TOP_DIRS,
            MATERIALIZATION_CLOSURE_FILE,
        )

        forbidden = FORBIDDEN_MATERIALIZED_TOP_DIRS
        for root_id in TEAM_ROOTS:
            with self.subTest(root_id=root_id):
                path = (
                    DOMAIN_KNOWLEDGE
                    / "curated"
                    / "by-root"
                    / root_id
                    / MATERIALIZATION_CLOSURE_FILE
                )
                if not path.is_file():
                    continue
                data = json.loads(path.read_text(encoding="utf-8"))
                for key in data:
                    if "/" not in key:
                        continue
                    top = key.split("/", 1)[0]
                    self.assertNotIn(
                        top,
                        forbidden,
                        f"{root_id}: legacy facet {top!r} in closure key {key!r}",
                    )
                    self.assertTrue(
                        top.startswith("facet-"),
                        f"{root_id}: key {key!r} missing facet- prefix",
                    )

    def test_materialized_tree_has_no_legacy_facet_dirs(self) -> None:
        from runtime.domain_knowledge_paths import FORBIDDEN_MATERIALIZED_TOP_DIRS, MATERIALIZED_BY_ROOT

        for root_dir in MATERIALIZED_BY_ROOT.iterdir():
            if not root_dir.is_dir():
                continue
            for legacy in FORBIDDEN_MATERIALIZED_TOP_DIRS:
                self.assertFalse(
                    (root_dir / legacy).is_dir(),
                    f"{root_dir.name}/{legacy} still exists",
                )

    def test_handoff_uses_canonical_paths(self) -> None:
        for root_id in TEAM_ROOTS:
            with self.subTest(root_id=root_id):
                path = DOMAIN_KNOWLEDGE / "extracted" / "by-root" / root_id / "PIPELINE_HANDOFF.json"
                if not path.is_file():
                    continue
                blob = path.read_text(encoding="utf-8")
                self.assertIn("materialized/by-root", blob)
                self.assertIn("curated/by-root", blob)
                self.assertNotIn("rules-distilled", blob)
                self.assertNotIn('"rules/by-root', blob)
                self.assertNotIn('"materialized/by-root', blob)


class TestContractDocsNaming(unittest.TestCase):
    def test_contract_files_use_canonical_naming(self) -> None:
        runbook = REPO / ".cursor/skills/generate-knowledge-from-wiki/RUNBOOK.md"
        skill = REPO / ".cursor/skills/generate-knowledge-from-wiki/SKILL.md"
        for path in CONTRACT_PATHS:
            with self.subTest(path=path.relative_to(REPO)):
                self.assertTrue(path.is_file(), path)
                text = path.read_text(encoding="utf-8")
                if path == runbook:
                    for token in REQUIRED_IN_RUNBOOK:
                        self.assertIn(token, text, f"missing {token!r} in {path.name}")
                if path == skill:
                    for token in REQUIRED_IN_SKILL:
                        self.assertIn(token, text, f"missing {token!r} in {path.name}")
                for token in FORBIDDEN_IN_CONTRACT:
                    self.assertNotIn(token, text, f"legacy {token!r} in {path.name}")
                extra = CONTRACT_EXTRA_REQUIRED.get(path.name, ())
                for token in extra:
                    self.assertIn(token, text, f"missing extra {token!r} in {path.name}")


class TestChecklistLoaderPaths(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _scripts_on_path()

    def test_checklist_path_uses_domain_module_checklist(self) -> None:
        from jira.lib.jira_checklist_themes import checklist_path
        from runtime.domain_knowledge_paths import DOMAIN_MODULE_CHECKLIST_FILE

        p = checklist_path("100001")
        self.assertIn(DOMAIN_MODULE_CHECKLIST_FILE, p.name)
        self.assertIn("curated", p.as_posix())


if __name__ == "__main__":
    unittest.main(verbosity=2)
