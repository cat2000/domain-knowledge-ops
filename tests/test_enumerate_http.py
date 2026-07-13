#!/usr/bin/env python3
"""Unit tests for wiki/lib/enumerate_http.py (CQL pagination, no live HTTP)."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from tests.contract_support import ensure_scripts_on_path

ensure_scripts_on_path()

from wiki.lib.enumerate_http import (  # noqa: E402
    _resolve_search_next_url,
    search_pages_cql,
)


class TestResolveSearchNextUrl(unittest.TestCase):
    def test_absolute_path(self) -> None:
        url = _resolve_search_next_url(
            "https://example.atlassian.net/wiki",
            "/rest/api/content/search?cursor=abc",
        )
        self.assertEqual(
            url,
            "https://example.atlassian.net/wiki/rest/api/content/search?cursor=abc",
        )


class TestSearchPagesCqlPagination(unittest.TestCase):
    @patch("wiki.lib.enumerate_http.req_json")
    def test_follows_links_next_until_exhausted(self, req_json) -> None:
        req_json.side_effect = [
            {
                "results": [{"id": "1"}, {"id": "2"}],
                "_links": {
                    "next": "/rest/api/content/search?cursor=page2",
                },
            },
            {
                "results": [{"id": "3"}],
                "_links": {},
            },
        ]
        rows = search_pages_cql(
            "https://example.atlassian.net/wiki",
            "Basic x",
            "type = page",
            250,
        )
        self.assertEqual([r["id"] for r in rows], ["1", "2", "3"])
        self.assertEqual(req_json.call_count, 2)
        second_url = req_json.call_args_list[1][0][0]
        self.assertIn("cursor=page2", second_url)

    @patch("wiki.lib.enumerate_http.req_json")
    def test_does_not_stop_when_first_batch_shorter_than_limit(self, req_json) -> None:
        """Regression: short first page + _links.next must not truncate results."""
        req_json.side_effect = [
            {
                "results": [{"id": str(i)} for i in range(98)],
                "_links": {
                    "next": "/rest/api/content/search?cursor=more",
                },
            },
            {
                "results": [{"id": "99"}, {"id": "100"}],
                "_links": {},
            },
        ]
        rows = search_pages_cql(
            "https://example.atlassian.net/wiki",
            "Basic x",
            "type = page",
            100,
        )
        self.assertEqual(len(rows), 100)
        self.assertEqual(req_json.call_count, 2)


if __name__ == "__main__":
    unittest.main()
