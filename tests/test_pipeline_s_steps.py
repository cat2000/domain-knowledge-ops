#!/usr/bin/env python3
"""
    Pipeline step naming: S1-S7 (no legacy Phase / 2a / 2b codes in contract layer).

Run from repo root:
  python3 -m unittest discover -s tests -p 'test_*.py' -v
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"

# Contract files that must use S1-S6 only (not domain-knowledge content under curated).
CONTRACT_PATHS = [
    REPO / ".cursor/skills/generate-knowledge-from-wiki/RUNBOOK.md",
    REPO / ".cursor/skills/generate-knowledge-from-wiki/SKILL.md",
    REPO / ".cursor/skills/generate-knowledge-from-wiki/S1-SYNC-CLI.md",
    REPO / ".cursor/skills/distill-domain-knowledge/SKILL.md",
    REPO / ".cursor/rules/domain-module-checklist.mdc",
    REPO / "domain-knowledge/DOMAIN_MODULE_CHECKLIST.template.md",
    REPO / "domain-knowledge/distill-quality-bar.md",
    REPO / "domain-knowledge/distill-document-skeleton.md",
    REPO / "scripts/wiki/sync/handoff.py",
    REPO / "scripts/distill/coverage.py",
    REPO / "scripts/distill/quality.py",
    REPO / "scripts/wiki/sync/pipeline.py",
    REPO / "TEAM_KNOWLEDGE_BASE.md",
    REPO / ".cursor/contracts/domain-knowledge-pipeline-contract.md",
]

LEGACY_STEP_TOKENS = (
    "2a-1",
    "2a-2",
    "2b-1",
    "2b-2",
    "Phase 1",
    "Phase 2",
    "第一大阶段",
    "第二大阶段",
)

EXPECTED_S_STEPS = ("S1", "S2", "S3", "S4", "S5", "S6", "S7")


def _scripts_on_path() -> None:
    s = str(SCRIPTS)
    if s not in sys.path:
        sys.path.insert(0, s)


class TestContractUsesSSteps(unittest.TestCase):
    def test_contract_files_have_no_legacy_step_codes(self) -> None:
        for path in CONTRACT_PATHS:
            with self.subTest(path=path.relative_to(REPO)):
                self.assertTrue(path.is_file(), path)
                text = path.read_text(encoding="utf-8")
                for token in LEGACY_STEP_TOKENS:
                    self.assertNotIn(
                        token,
                        text,
                        f"{path.name} still contains legacy token {token!r}",
                    )

    def test_skill_forbids_translation_through_s5(self) -> None:
        skill = (REPO / ".cursor/skills/generate-knowledge-from-wiki/SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("No translation in S1–S6", skill)
        self.assertIn("S7", skill)
        self.assertNotIn("S1–S3 禁止翻译", skill)

    def test_runbook_defines_all_s_steps(self) -> None:
        runbook = (REPO / ".cursor/skills/generate-knowledge-from-wiki/RUNBOOK.md").read_text(
            encoding="utf-8"
        )
        for step in EXPECTED_S_STEPS:
            self.assertIn(step, runbook)


class TestHandoffSSteps(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _scripts_on_path()

    def test_write_handoff_s1_through_s7(self) -> None:
        from wiki.sync.handoff import write_pipeline_handoff

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            extracted = tmp_path / "extracted"
            rules = tmp_path / "rules"
            extracted.mkdir()
            rules.mkdir()
            with patch("wiki.sync.handoff.REPO_ROOT", tmp_path):
                path = write_pipeline_handoff("100001", extracted, rules)
            payload = json.loads(path.read_text(encoding="utf-8"))
            phases = payload["distill_phases"]
            contract = payload["chaining_contract"]
            for step in EXPECTED_S_STEPS:
                self.assertIn(step, phases, phases)
            self.assertIn("确认", contract)
            self.assertTrue(payload.get("s1_complete"))
            self.assertIn("cursor_skill", payload)
            self.assertNotIn("stage1_complete", payload)

    def test_team_handoffs_on_disk(self) -> None:
        for root_id in ("100001",):
            with self.subTest(root_id=root_id):
                path = REPO / f"domain-knowledge/extracted/by-root/{root_id}/PIPELINE_HANDOFF.json"
                if not path.is_file():
                    continue
                payload = json.loads(path.read_text(encoding="utf-8"))
                blob = json.dumps(payload, ensure_ascii=False)
                for step in EXPECTED_S_STEPS:
                    self.assertIn(step, blob)
                for token in LEGACY_STEP_TOKENS:
                    self.assertNotIn(token, blob)


if __name__ == "__main__":
    unittest.main(verbosity=2)
