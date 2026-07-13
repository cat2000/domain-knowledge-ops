#!/usr/bin/env python3
"""Unit tests for jira/lib/jira_materialize_logic.py."""

from __future__ import annotations

import unittest

from tests.contract_support import ensure_scripts_on_path

ensure_scripts_on_path()

from jira.lib.jira_materialize_logic import raw_ticket_to_markdown  # noqa: E402


class TestRawTicketToMarkdown(unittest.TestCase):
    def test_renders_description_and_comments(self) -> None:
        doc = {
            "key": "DEV-1",
            "summary": "Checkout flow",
            "status": "Done",
            "issuetype": "Story",
            "parent_key": "EPIC-9",
            "parent": {"key": "EPIC-9", "summary": "Checkout epic"},
            "description_text": "User must pay",
            "comments": [
                {
                    "author": "Alice",
                    "created": "2026-01-01",
                    "body_text": "AC: show FPV",
                }
            ],
        }
        text = raw_ticket_to_markdown(doc)
        self.assertIn("key: DEV-1", text)
        self.assertIn("# DEV-1 · Checkout flow", text)
        self.assertIn("User must pay", text)
        self.assertIn("AC: show FPV", text)
        self.assertIn("## Comments (1)", text)


if __name__ == "__main__":
    unittest.main()
