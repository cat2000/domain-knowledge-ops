#!/usr/bin/env python3
"""Unit tests for jira/lib/jira_fetch_logic.py (no Jira HTTP)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tests.contract_support import ensure_scripts_on_path

ensure_scripts_on_path()

from jira.lib.jira_fetch_logic import (  # noqa: E402
    adf_to_text,
    build_parent_index,
    field_text,
    parse_keys_arg,
    should_advance_fetch_window,
)


class TestAdfToText(unittest.TestCase):
    def test_plain_text_node(self) -> None:
        self.assertEqual(adf_to_text({"type": "text", "text": "hello"}), "hello")

    def test_paragraph_adds_newline(self) -> None:
        node = {
            "type": "paragraph",
            "content": [{"type": "text", "text": "line"}],
        }
        self.assertEqual(adf_to_text(node), "line\n")

    def test_nested_list(self) -> None:
        doc = [
            {"type": "text", "text": "a"},
            {"type": "text", "text": "b"},
        ]
        self.assertEqual(adf_to_text(doc), "a\nb")


class TestFieldText(unittest.TestCase):
    def test_string_stripped(self) -> None:
        self.assertEqual(field_text("  x  "), "x")

    def test_adf_dict(self) -> None:
        self.assertEqual(
            field_text({"type": "paragraph", "content": [{"type": "text", "text": "d"}]}),
            "d",
        )

    def test_none_is_empty(self) -> None:
        self.assertEqual(field_text(None), "")


class TestBuildParentIndex(unittest.TestCase):
    def test_groups_children_by_parent_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp)
            (raw / "A.json").write_text(
                json.dumps({"key": "A", "parent_key": "EPIC-1", "parent": {"key": "EPIC-1"}}),
                encoding="utf-8",
            )
            (raw / "B.json").write_text(
                json.dumps({"key": "B", "parent_key": "EPIC-1"}),
                encoding="utf-8",
            )
            idx = build_parent_index(raw)
            self.assertEqual(idx["child_count"], 2)
            slot = idx["by_parent"]["EPIC-1"]
            self.assertEqual(sorted(slot["children"]), ["A", "B"])


class TestParseKeysArg(unittest.TestCase):
    def test_splits_whitespace_and_commas(self) -> None:
        self.assertEqual(parse_keys_arg("dev-1, DEV-2\nDEV-3"), ["DEV-1", "DEV-2", "DEV-3"])


class TestShouldAdvanceFetchWindow(unittest.TestCase):
    def test_batch_mode_with_full_batch_and_cursor_waits(self) -> None:
        self.assertFalse(
            should_advance_fetch_window(
                "history", batch_count=50, limit=50, cursor={"last_key": "X-1"}
            )
        )

    def test_history_mode_without_cursor_can_advance(self) -> None:
        self.assertTrue(
            should_advance_fetch_window("history", batch_count=10, limit=50, cursor={})
        )

    def test_sprint_mode_never_advances(self) -> None:
        self.assertFalse(
            should_advance_fetch_window("sprint", batch_count=0, limit=50, cursor={})
        )


if __name__ == "__main__":
    unittest.main()
