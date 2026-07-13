#!/usr/bin/env python3
"""Unit tests for wiki/lib/enumerate_logic.py (no Confluence HTTP)."""

from __future__ import annotations

import unittest

from tests.contract_support import ensure_scripts_on_path

ensure_scripts_on_path()

from wiki.lib.enumerate_logic import (  # noqa: E402
    compact_row,
    merge_enum_root_row,
)


class TestCompactRow(unittest.TestCase):
    def test_builds_web_ui_from_links(self) -> None:
        row = compact_row(
            {
                "id": "123",
                "title": "Hello",
                "space": {"key": "CMA"},
                "_links": {"webui": "/spaces/CMA/pages/123/Title"},
            },
            "https://example.atlassian.net/wiki",
        )
        self.assertEqual(row["id"], "123")
        self.assertEqual(row["title"], "Hello")
        self.assertEqual(row["spaceKey"], "CMA")
        self.assertEqual(
            row["webUi"],
            "https://example.atlassian.net/wiki/spaces/CMA/pages/123/Title",
        )

    def test_fallback_web_ui_from_space_key(self) -> None:
        row = compact_row(
            {"id": "99", "title": "T", "space": {"key": "CHIN"}},
            "https://example.atlassian.net/wiki",
        )
        self.assertIn("/spaces/CHIN/pages/99/", row["webUi"])


class TestMergeEnumRootRow(unittest.TestCase):
    def test_prepends_when_root_missing(self) -> None:
        root = {"id": "1", "title": "Root", "spaceKey": "CMA", "webUi": "https://x/1"}
        merged = merge_enum_root_row([{"id": "2", "title": "Child"}], "1", root)
        self.assertEqual([r["id"] for r in merged], ["1", "2"])

    def test_noop_when_root_present(self) -> None:
        rows = [{"id": "1", "title": "Root"}, {"id": "2", "title": "Child"}]
        merged = merge_enum_root_row(rows, "1", {"id": "1", "title": "Root"})
        self.assertEqual(len(merged), 2)
        self.assertIs(merged, rows)


if __name__ == "__main__":
    unittest.main()
