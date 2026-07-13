#!/usr/bin/env python3
"""Unit tests for jira/lib/jira_attachment_logic.py."""

from __future__ import annotations

import unittest

from tests.contract_support import ensure_scripts_on_path

ensure_scripts_on_path()

from jira.lib.jira_attachment_logic import (  # noqa: E402
    build_comments_digest,
    html_rendered_to_plain,
)


class TestHtmlRenderedToPlain(unittest.TestCase):
    def test_strips_tags(self) -> None:
        plain = html_rendered_to_plain("<p>Hello <b>world</b></p>")
        self.assertIn("Hello", plain)
        self.assertIn("world", plain)
        self.assertNotIn("<p>", plain)


class TestBuildCommentsDigest(unittest.TestCase):
    def test_empty_comments(self) -> None:
        text = build_comments_digest("DEV-1", {"comments": []})
        self.assertIn("DEV-1", text)
        self.assertIn("(无评论)", text)


if __name__ == "__main__":
    unittest.main()
