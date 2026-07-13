#!/usr/bin/env python3
"""Unit tests for wiki/lib/source_coverage_logic.py."""

from __future__ import annotations

import unittest

from tests.contract_support import ensure_scripts_on_path

ensure_scripts_on_path()

from wiki.lib.source_coverage_logic import (  # noqa: E402
    render_source_coverage_markdown,
    title_for_table,
)


def stub_classify(title: str, snippet: str) -> tuple[str, str]:
    return ("theme-x", "kb/path")


class TestRenderSourceCoverage(unittest.TestCase):
    def test_renders_table_row(self) -> None:
        rows = [{"id": "2", "title": "T2", "webUi": "https://x/2"}, {"id": "1", "title": "T1"}]
        text = render_source_coverage_markdown(
            rows,
            classify=stub_classify,
            root_page_id="999",
            root_url="https://root",
            root_label="Root",
        )
        self.assertIn("| 1 | theme-x | `kb/path` | T1 | `1` |", text)
        self.assertIn("共 **2** 页", text)

    def test_title_for_table_prefers_none_without_pages_dir(self) -> None:
        self.assertEqual(title_for_table(None, "1", "API"), "API")


if __name__ == "__main__":
    unittest.main()
