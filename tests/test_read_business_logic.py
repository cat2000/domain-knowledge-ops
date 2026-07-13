#!/usr/bin/env python3
"""Unit tests for jira/lib/read_business_logic.py."""

from __future__ import annotations

import unittest

from tests.contract_support import ensure_scripts_on_path

ensure_scripts_on_path()

from jira.lib.read_business_logic import (  # noqa: E402
    full_text,
    scan_theme,
    text_length,
    themes_from_attribution,
)


class TestFullText(unittest.TestCase):
    def test_joins_summary_description_comments(self) -> None:
        raw = {
            "summary": "S",
            "description_text": "D",
            "comments": [{"body_text": "C1"}, {"body_text": "C2"}],
        }
        self.assertIn("S", full_text(raw))
        self.assertIn("C2", full_text(raw))


class TestScanTheme(unittest.TestCase):
    def test_clusters_checkout_pattern_default_locale_en(self) -> None:
        keys = ["DEV-1", "DEV-2"]
        raw_by_key = {
            "DEV-1": {"summary": "CNCheckout flow", "description_text": "", "comments": []},
            "DEV-2": {"summary": "unrelated", "description_text": "misc", "comments": []},
        }
        text = scan_theme("checkout", keys, raw_by_key, {}, {"DEV-1": {}, "DEV-2": {}})
        self.assertIn("CNCheckout/Epic68638", text)
        self.assertIn("Unmatched by clusters above", text)

    def test_substance_sorted_desc_en(self) -> None:
        keys = ["A", "B"]
        raw_by_key = {
            "A": {"summary": "short", "description_text": "x" * 90, "comments": []},
            "B": {"summary": "long", "description_text": "y" * 200, "comments": []},
        }
        text = scan_theme("checkout", keys, raw_by_key, {}, {"A": {}, "B": {}})
        substance_start = text.index("Substantive tickets")
        substance_end = text.index("## Clustered by parent Epic")
        block = text[substance_start:substance_end]
        self.assertLess(
            block.index("https://your-site.atlassian.net/browse/B"),
            block.index("https://your-site.atlassian.net/browse/A"),
        )

    def test_clusters_checkout_pattern_zh(self) -> None:
        keys = ["DEV-1", "DEV-2"]
        raw_by_key = {
            "DEV-1": {"summary": "CNCheckout flow", "description_text": "", "comments": []},
            "DEV-2": {"summary": "unrelated", "description_text": "misc", "comments": []},
        }
        text = scan_theme(
            "checkout", keys, raw_by_key, {}, {"DEV-1": {}, "DEV-2": {}}, locale="zh-CN"
        )
        self.assertIn("CNCheckout/Epic68638", text)
        self.assertIn("未命中上述簇", text)

    def test_substance_sorted_desc_zh(self) -> None:
        keys = ["A", "B"]
        raw_by_key = {
            "A": {"summary": "short", "description_text": "x" * 90, "comments": []},
            "B": {"summary": "long", "description_text": "y" * 200, "comments": []},
        }
        text = scan_theme("checkout", keys, raw_by_key, {}, {"A": {}, "B": {}}, locale="zh-CN")
        substance_start = text.index("正文充实票")
        substance_end = text.index("## 按父 Epic")
        block = text[substance_start:substance_end]
        self.assertLess(
            block.index("https://your-site.atlassian.net/browse/B"),
            block.index("https://your-site.atlassian.net/browse/A"),
        )


class TestThemesFromAttribution(unittest.TestCase):
    def test_collects_primary_and_themes_in_allowed(self) -> None:
        tickets = {
            "DEV-1": {"primary": "checkout", "themes": ["contests"]},
            "DEV-2": {"primary": "gateway", "themes": []},
        }
        allowed = frozenset({"checkout", "contests", "gateway", "requirements"})
        self.assertEqual(
            themes_from_attribution(tickets, allowed),
            ["checkout", "contests", "gateway"],
        )

    def test_empty_when_no_overlap(self) -> None:
        self.assertEqual(themes_from_attribution({"K": {"primary": "x"}}, frozenset()), [])


class TestTextLength(unittest.TestCase):
    def test_counts_description_and_comments(self) -> None:
        raw = {"description_text": "abc", "comments": [{"body_text": "de"}]}
        self.assertEqual(text_length(raw), 5)


if __name__ == "__main__":
    unittest.main()
