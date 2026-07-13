#!/usr/bin/env python3
"""Unit tests for wiki/lib/extract_logic.py (no Confluence HTTP)."""

from __future__ import annotations

import unittest

from tests.contract_support import ensure_scripts_on_path

ensure_scripts_on_path()

from wiki.lib.extract_logic import (  # noqa: E402
    auto_extract_workers,
    choose_extract_workers,
    parse_page_id_list,
    pick_body,
)


class TestParsePageIdList(unittest.TestCase):
    def test_splits_comma_and_semicolon(self) -> None:
        self.assertEqual(parse_page_id_list("1, 2;3"), {"1", "2", "3"})

    def test_ignores_non_digits(self) -> None:
        self.assertEqual(parse_page_id_list("abc, 42"), {"42"})

    def test_empty_returns_empty_set(self) -> None:
        self.assertEqual(parse_page_id_list(""), set())


class TestAutoExtractWorkers(unittest.TestCase):
    def test_single_page_is_sequential(self) -> None:
        self.assertEqual(auto_extract_workers(1), 1)

    def test_many_pages_bounded_by_hw_cap(self) -> None:
        w = auto_extract_workers(200, cpu_count=4, max_workers_cap=16)
        self.assertGreaterEqual(w, 2)
        self.assertLessEqual(w, 16)

    def test_small_page_count_respects_cpu(self) -> None:
        w = auto_extract_workers(20, cpu_count=2, max_workers_cap=16)
        self.assertLessEqual(w, 4)


class TestChooseExtractWorkers(unittest.TestCase):
    def test_cli_overrides_auto(self) -> None:
        workers, reason = choose_extract_workers(100, cli=3)
        self.assertEqual(workers, 3)
        self.assertEqual(reason, "--workers")

    def test_env_overrides_auto(self) -> None:
        workers, reason = choose_extract_workers(100, env_workers=5)
        self.assertEqual(workers, 5)
        self.assertEqual(reason, "CONFLUENCE_EXTRACT_WORKERS")

    def test_auto_reason_includes_page_count(self) -> None:
        workers, reason = choose_extract_workers(32)
        self.assertGreaterEqual(workers, 1)
        self.assertIn("32 pages", reason)


class TestPickBody(unittest.TestCase):
    def test_prefers_view_html(self) -> None:
        data = {
            "body": {
                "view": {"value": "<p>Hello from view with enough text for the view path.</p>"},
                "storage": {"value": "<p>Storage fallback</p>"},
            }
        }
        text, source, note = pick_body(data)
        self.assertIn("Hello from view", text)
        self.assertEqual(source, "view")
        self.assertEqual(note, "")

    def test_falls_back_to_storage_when_view_empty(self) -> None:
        data = {"body": {"view": {"value": ""}, "storage": {"value": "<p>Only storage</p>"}}}
        text, source, _ = pick_body(data)
        self.assertIn("Only storage", text)
        self.assertEqual(source, "storage")

    def test_empty_body_returns_note(self) -> None:
        text, source, note = pick_body({"body": {}})
        self.assertEqual(text, "")
        self.assertEqual(source, "empty")
        self.assertIn("body.view", note)


if __name__ == "__main__":
    unittest.main()
