#!/usr/bin/env python3
"""
Regression tests for 确认 / two-stage pipeline rename (2026-05).

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

TEAM_ROOTS = {"demo": "100001"}

# Expected confirmed slugs when a checklist exists under curated/by-root/<root_id>/.
EXPECTED_CONFIRMED = {
    "100001": {
        "checkout",
        "compensation-cbp",
        "contests",
        "compliance-identity",
        "messaging",
    },
}


def _scripts_on_path() -> None:
    s = str(SCRIPTS)
    if s not in sys.path:
        sys.path.insert(0, s)


class TestConfirmedThemesLoader(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _scripts_on_path()

    def test_load_confirmed_themes_matches_checklist(self) -> None:
        from jira.lib.jira_checklist_themes import (
            _status_is_confirmed,
            load_confirmed_themes,
            parse_checklist_rows,
        )

        for root_id in TEAM_ROOTS.values():
            with self.subTest(root_id=root_id):
                path = REPO / f"domain-knowledge/curated/by-root/{root_id}/DOMAIN_MODULE_CHECKLIST.md"
                if not path.is_file():
                    continue
                expected = {
                    slug
                    for slug, status in parse_checklist_rows(path.read_text(encoding="utf-8"))
                    if _status_is_confirmed(status)
                }
                slugs = set(load_confirmed_themes(root_id))
                self.assertEqual(slugs, expected)

    def test_legacy_status_认真稿_not_confirmed(self) -> None:
        from jira.lib.jira_checklist_themes import parse_checklist_rows, _status_is_confirmed

        md = """
| 主题 | 命题 slug | strategy 维度 | 扫描 | 主入口 | 状态 | 术语备注 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 测试 | `legacy-slug` | x | `foo/` | `_deliver/legacy-slug/x.md` | 认真稿 | | |
| 新 | `new-slug` | x | `bar/` | `_deliver/new-slug/x.md` | 确认 | | |
| 待确认 | `draft-slug` | x | `baz/` | `_deliver/draft-slug/x.md` | 待确认 | | |
"""
        rows = dict(parse_checklist_rows(md))
        self.assertFalse(_status_is_confirmed(rows["legacy-slug"]))
        self.assertTrue(_status_is_confirmed(rows["new-slug"]))
        self.assertFalse(_status_is_confirmed(rows["draft-slug"]))

    def test_load_confirmed_from_synthetic_checklist(self) -> None:
        from jira.lib.jira_checklist_themes import load_confirmed_themes

        md = """
### A
- **命题 slug**: `alpha`
- **strategy 维度**: x
- **领域子目录（扫描）**:
- **主入口**: `_deliver/alpha/x.md`
- **状态**: 确认
- **术语备注**:
- **备注**:

### B
- **命题 slug**: `beta`
- **strategy 维度**: x
- **领域子目录（扫描）**:
- **主入口**: `_deliver/beta/x.md`
- **状态**: 待确认
- **术语备注**:
- **备注**:
"""
        with tempfile.TemporaryDirectory() as tmp:
            root_id = "99999999"
            base = Path(tmp) / "domain-knowledge/curated/by-root" / root_id
            base.mkdir(parents=True)
            (base / "DOMAIN_MODULE_CHECKLIST.md").write_text(md, encoding="utf-8")
            with patch("jira.lib.jira_checklist_themes.REPO_ROOT", Path(tmp)):
                self.assertEqual(load_confirmed_themes(root_id), ["alpha"])

    def test_missing_checklist_returns_empty(self) -> None:
        from jira.lib.jira_checklist_themes import load_confirmed_themes

        self.assertEqual(load_confirmed_themes("00000000"), [])


class TestNormativePrimaries(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _scripts_on_path()

    def test_normative_primaries_includes_confirmed_slugs(self) -> None:
        from jira.lib.jira_team_attribution import normative_primaries
        from jira.lib.jira_checklist_themes import load_confirmed_themes
        from teams.registry import resolve_team

        for team, root_id in TEAM_ROOTS.items():
            with self.subTest(team=team):
                _, cfg = resolve_team(team)
                primaries = normative_primaries(cfg, root_id)
                for slug in load_confirmed_themes(root_id):
                    self.assertIn(slug, primaries)


class TestPipelineHandoff(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _scripts_on_path()

    def test_write_handoff_two_stage_contract(self) -> None:
        from wiki.sync.handoff import write_pipeline_handoff

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            extracted = tmp_path / "extracted"
            rules = tmp_path / "rules"
            extracted.mkdir()
            rules.mkdir()
            root_id = "100001"
            with patch("wiki.sync.handoff.REPO_ROOT", tmp_path):
                path = write_pipeline_handoff(root_id, extracted, rules)
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertTrue(payload["s1_complete"])
            self.assertEqual(payload["s1_status"], "complete")
            self.assertIn("S2", payload["distill_phases"])
            self.assertIn("确认", payload["distill_phases"])
            self.assertIn("确认", payload["chaining_contract"])
            self.assertIn("S3", payload["chaining_contract"])

    def test_write_handoff_partial_blocks_by_contract(self) -> None:
        from wiki.sync.handoff import write_pipeline_handoff

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            extracted = tmp_path / "extracted"
            rules = tmp_path / "rules"
            extracted.mkdir()
            rules.mkdir()
            with patch("wiki.sync.handoff.REPO_ROOT", tmp_path):
                path = write_pipeline_handoff(
                    "100001",
                    extracted,
                    rules,
                    s1_status="partial",
                    extract_error_count=2,
                )
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertFalse(payload["s1_complete"])
            self.assertEqual(payload["s1_status"], "partial")
            self.assertEqual(payload["extract_error_count"], 2)
            self.assertIn("partial S1 handoff blocks S2", payload["chaining_contract"])

    def test_existing_team_handoffs_have_confirm_contract(self) -> None:
        for root_id in TEAM_ROOTS.values():
            with self.subTest(root_id=root_id):
                path = REPO / f"domain-knowledge/extracted/by-root/{root_id}/PIPELINE_HANDOFF.json"
                if not path.is_file():
                    continue
                payload = json.loads(path.read_text(encoding="utf-8"))
                contract = payload.get("chaining_contract", "")
                phases = payload.get("distill_phases", "")
                self.assertIn("确认", contract + phases)
                self.assertNotIn("认真稿", contract + phases)
                for token in ("2a-1", "2b-2", "Phase 1"):
                    self.assertNotIn(token, contract + phases)
                for step in ("S1", "S2", "S3", "S4", "S5", "S6"):
                    self.assertIn(step, contract + phases)


class TestChecklistOnDisk(unittest.TestCase):
    def test_team_checklists_use_confirm_status_not_legacy_only(self) -> None:
        for root_id in TEAM_ROOTS.values():
            with self.subTest(root_id=root_id):
                path = REPO / f"domain-knowledge/curated/by-root/{root_id}/DOMAIN_MODULE_CHECKLIST.md"
                if not path.is_file():
                    continue
                text = path.read_text(encoding="utf-8")
                self.assertIn("确认", text)
                # Title reflects 领域模块确认页
                self.assertIn("领域模块确认页", text)


class TestJiraCheckPipelineConfirmed(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _scripts_on_path()

    def test_confirmed_themes_helper(self) -> None:
        from jira.lib.jira_checklist_themes import load_confirmed_themes
        from jira.lib.jira_checklist_themes import parse_checklist_rows, _status_is_confirmed

        root_id = TEAM_ROOTS["demo"]
        path = REPO / f"domain-knowledge/curated/by-root/{root_id}/DOMAIN_MODULE_CHECKLIST.md"
        if not path.is_file():
            self.skipTest(f"Checklist not materialized for root {root_id}")
        expected = {
            slug
            for slug, status in parse_checklist_rows(path.read_text(encoding="utf-8"))
            if _status_is_confirmed(status)
        }
        slugs = set(load_confirmed_themes(root_id))
        self.assertEqual(slugs, expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
