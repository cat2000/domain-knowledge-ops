#!/usr/bin/env python3
"""Tests for deliverable-locale-tokens.json and deliverable_locale.py loader."""

from __future__ import annotations

import sys
import unittest

from tests.contract_support import ensure_scripts_on_path

ensure_scripts_on_path()


class TestDeliverableLocaleTokenMap(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        ensure_scripts_on_path()

    def _loader(self):
        from runtime import deliverable_locale
        # Clear lru_cache so tests always read from disk.
        deliverable_locale.load_token_map.cache_clear()
        return deliverable_locale

    def test_both_locales_present(self) -> None:
        m = self._loader()
        data = m.load_token_map()
        locales = data.get("locales", {})
        self.assertIn("en", locales, "en locale missing from token map")
        self.assertIn("zh-CN", locales, "zh-CN locale missing from token map")

    def test_version_field(self) -> None:
        m = self._loader()
        data = m.load_token_map()
        self.assertEqual(data.get("version"), 1)

    def test_token_en_s5_domain_model(self) -> None:
        m = self._loader()
        result = m.token("s5_headings.domain_model", "en")
        self.assertEqual(result, "## Domain model")

    def test_token_zh_s5_domain_model_contains_cjk(self) -> None:
        m = self._loader()
        result = m.token("s5_headings.domain_model", "zh-CN")
        self.assertIn("领域模型", result)

    def test_all_locale_values_returns_both(self) -> None:
        m = self._loader()
        values = m.all_locale_values("s5_headings.domain_model")
        self.assertIn("## Domain model", values)
        self.assertTrue(any("领域模型" in v for v in values))

    def test_all_locale_values_deduped(self) -> None:
        m = self._loader()
        values = m.all_locale_values("s5_headings.provenance")
        # Values should be unique even if both locales share the same string.
        self.assertEqual(len(values), len(set(values)))

    def test_s7_decision_card_en(self) -> None:
        m = self._loader()
        self.assertEqual(m.token("s7_decision_card_labels.confirmed_rule", "en"), "Confirmed rule")
        self.assertEqual(m.token("s7_decision_card_labels.open_boundary", "en"), "Open boundary")
        self.assertEqual(m.token("s7_decision_card_labels.user_visible_effect", "en"), "User-visible effect")
        self.assertEqual(m.token("s7_decision_card_labels.linked_open_items", "en"), "Linked open items")

    def test_s7_decision_card_zh(self) -> None:
        m = self._loader()
        self.assertEqual(m.token("s7_decision_card_labels.confirmed_rule", "zh-CN"), "已确认规则")

    def test_work_draft_globs_returns_both_locales(self) -> None:
        m = self._loader()
        globs = m.work_draft_globs()
        self.assertIn("*work-draft.md", globs)
        self.assertIn("*领域知识-工作稿.md", globs)

    def test_locale_brief_globs_returns_both_locales(self) -> None:
        m = self._loader()
        globs = m.locale_brief_globs()
        self.assertIn("*domain-brief.md", globs)
        self.assertIn("*领域知识定稿.md", globs)

    def test_default_locale_reads_team_roots(self) -> None:
        m = self._loader()
        locale = m.default_locale()
        # team-roots.json has defaults.deliverable_locale = "en"
        self.assertIn(locale, ("en", "zh-CN"), f"unexpected locale: {locale}")

    def test_locale_tokens_returns_dict(self) -> None:
        m = self._loader()
        tokens = m.locale_tokens("en")
        self.assertIsInstance(tokens, dict)
        self.assertIn("s5_headings", tokens)
        self.assertIn("filenames", tokens)

    def test_heading_matchers_alias(self) -> None:
        m = self._loader()
        self.assertEqual(
            m.heading_matchers("s5_headings.closed_chains"),
            m.all_locale_values("s5_headings.closed_chains"),
        )

    def test_token_missing_path_returns_empty(self) -> None:
        m = self._loader()
        self.assertEqual(m.token("nonexistent.path", "en"), "")

    def test_checklist_field_slug_en(self) -> None:
        m = self._loader()
        self.assertEqual(m.token("checklist.field_slug", "en"), "Proposition slug")

    def test_checklist_field_slug_zh(self) -> None:
        m = self._loader()
        self.assertEqual(m.token("checklist.field_slug", "zh-CN"), "命题 slug")

    def test_gap_scan_filename_en(self) -> None:
        m = self._loader()
        self.assertEqual(m.gap_scan_filename("en"), "gap-scan.md")

    def test_gap_scan_filename_zh(self) -> None:
        m = self._loader()
        self.assertEqual(m.gap_scan_filename("zh-CN"), "遗漏扫描.md")

    def test_gap_scan_filename_defaults_to_default_locale(self) -> None:
        m = self._loader()
        self.assertEqual(m.gap_scan_filename(), m.gap_scan_filename(m.default_locale()))

    def test_full_key_index_filename_en(self) -> None:
        m = self._loader()
        self.assertEqual(m.full_key_index_filename("en"), "full-key-index.md")

    def test_full_key_index_filename_zh(self) -> None:
        m = self._loader()
        self.assertEqual(m.full_key_index_filename("zh-CN"), "全量KEY索引.md")


class TestIsChecklistStatusConfirmed(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        ensure_scripts_on_path()

    def _fn(self):
        from runtime.domain_knowledge_paths import is_checklist_status_confirmed
        return is_checklist_status_confirmed

    def test_zh_confirmed(self) -> None:
        fn = self._fn()
        self.assertTrue(fn("确认"))
        self.assertTrue(fn("**确认**"))

    def test_zh_pending_rejected(self) -> None:
        fn = self._fn()
        self.assertFalse(fn("待确认"))

    def test_en_confirmed(self) -> None:
        fn = self._fn()
        self.assertTrue(fn("confirmed"))
        self.assertTrue(fn("confirm"))

    def test_en_pending_rejected(self) -> None:
        fn = self._fn()
        self.assertFalse(fn("pending"))

    def test_empty_and_dashes_rejected(self) -> None:
        fn = self._fn()
        self.assertFalse(fn(""))
        self.assertFalse(fn("—"))
        self.assertFalse(fn("-"))
        self.assertFalse(fn("不归档"))


if __name__ == "__main__":
    unittest.main()
