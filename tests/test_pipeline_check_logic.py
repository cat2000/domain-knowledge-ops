#!/usr/bin/env python3
"""Unit tests for jira/lib/pipeline_check_logic.py."""

from __future__ import annotations

import unittest

from tests.contract_support import ensure_scripts_on_path

ensure_scripts_on_path()

from jira.lib.pipeline_check_logic import (  # noqa: E402
    FORBIDDEN_THEME_SLUGS,
    issues_for_attribution,
    issues_for_raw_ticket,
)


class TestIssuesForRawTicket(unittest.TestCase):
    def test_missing_file(self) -> None:
        self.assertIn("missing raw", issues_for_raw_ticket("DEV-1", None, False)[0])

    def test_requires_description_and_comments(self) -> None:
        issues = issues_for_raw_ticket("DEV-1", {"summary": "x"}, True)
        self.assertTrue(any("description_text" in issue for issue in issues))
        self.assertTrue(any("comments" in issue for issue in issues))


class TestIssuesForAttribution(unittest.TestCase):
    def test_forbidden_primary(self) -> None:
        issues = issues_for_attribution(
            "DEV-1",
            {
                "primary": "mall-app",
                "themes": ["checkout"],
                "product_line": "demo",
                "material_kind": "req",
                "substance_tier": "high",
                "distill_tier": "index_only",
            },
            allowed={"checkout"},
        )
        self.assertTrue(any("product channel" in issue for issue in issues))

    def test_requires_distill_tier(self) -> None:
        issues = issues_for_attribution(
            "DEV-1",
            {
                "primary": "checkout",
                "themes": ["checkout"],
                "product_line": "demo",
                "material_kind": "req",
                "substance_tier": "high",
            },
            allowed={"checkout"},
        )
        self.assertTrue(any("distill_tier" in issue for issue in issues))


class TestForbiddenSlugs(unittest.TestCase):
    def test_mall_app_forbidden(self) -> None:
        self.assertIn("mall-app", FORBIDDEN_THEME_SLUGS)


if __name__ == "__main__":
    unittest.main()
