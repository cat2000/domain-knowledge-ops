#!/usr/bin/env python3
"""Unit tests for jira attribute_logic (no filesystem / LLM)."""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tests.contract_support import ensure_scripts_on_path

ensure_scripts_on_path()

from jira.lib.attribute_logic import (  # noqa: E402
    result_to_yaml,
    should_preserve_attr,
    yaml_quote,
)
from jira.lib.jira_first_principles import AttributionResult  # noqa: E402


def _sample_result() -> AttributionResult:
    return AttributionResult(
        key="DEV-1",
        type="Story",
        parent=None,
        hierarchy_root=None,
        parent_summary="",
        themes=["gateway"],
        primary="gateway",
        product_line="demo",
        material_kind="requirement",
        signal="normative",
        confidence="high",
        substance_chars=120,
        substance_tier="substantive",
        distill_queue=True,
        distill_tier="proposition",
        proposition_id="prop-1",
        proposition_extract=True,
        effective_at="2024-01-01",
        attribution_method="first_principles",
        related_keys=[],
        comment_count=2,
        wiki_gap=False,
        spike_role=None,
        business_extract=False,
        one_line="One line",
        attribution_notes="",
    )


class TestYamlQuote(unittest.TestCase):
    def test_null_and_bool(self) -> None:
        self.assertEqual(yaml_quote(None), "null")
        self.assertEqual(yaml_quote(True), "true")

    def test_quotes_special_chars(self) -> None:
        self.assertEqual(yaml_quote("a: b"), '"a: b"')


class TestShouldPreserveAttr(unittest.TestCase):
    def test_false_when_missing_file(self) -> None:
        self.assertFalse(should_preserve_attr(Path("/no/such/file.yaml")))

    def test_true_for_cursor_review_v2(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "DEV-1.yaml"
            path.write_text(
                "attribution_method: cursor_review\nproduct_line: demo\nmaterial_kind: req\n",
                encoding="utf-8",
            )
            self.assertTrue(should_preserve_attr(path))


class TestResultToYaml(unittest.TestCase):
    def test_includes_key_and_themes(self) -> None:
        text = result_to_yaml(_sample_result(), "2024-06-01T00:00:00Z")
        self.assertIn("key: DEV-1", text)
        self.assertIn("themes:", text)
        self.assertIn("  - gateway", text)


if __name__ == "__main__":
    unittest.main()
