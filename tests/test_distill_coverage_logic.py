#!/usr/bin/env python3
"""Unit tests for distill/coverage_logic.py (pure functions, no domain-knowledge disk)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests.contract_support import ensure_scripts_on_path

ensure_scripts_on_path()

from distill.coverage_logic import (  # noqa: E402
    evaluate_strict_violations,
    looks_like_pass_stub_file,
    looks_like_pass_stub_text,
    normalize_closure_value,
    rules_only_pass_ratio,
)
from runtime.domain_knowledge_paths import NON_BUSINESS_HEADING  # noqa: E402

PASS_HEADINGS = frozenset({NON_BUSINESS_HEADING})


class TestNormalizeClosureValue(unittest.TestCase):
    def test_single_string_path(self) -> None:
        self.assertEqual(normalize_closure_value("deliver/foo.md"), ["deliver/foo.md"])

    def test_normalizes_backslashes(self) -> None:
        self.assertEqual(normalize_closure_value("deliver\\foo.md"), ["deliver/foo.md"])

    def test_list_of_paths(self) -> None:
        self.assertEqual(
            normalize_closure_value(["a.md", "b.md"]),
            ["a.md", "b.md"],
        )

    def test_rejects_empty_string(self) -> None:
        with self.assertRaises(ValueError):
            normalize_closure_value("  ")

    def test_rejects_empty_list(self) -> None:
        with self.assertRaises(ValueError):
            normalize_closure_value([])

    def test_rejects_invalid_type(self) -> None:
        with self.assertRaises(ValueError):
            normalize_closure_value({"path": "x.md"})


class TestPassStubHeuristics(unittest.TestCase):
    def test_detects_pass_heading_in_text(self) -> None:
        body = f"# Title\n\n{NON_BUSINESS_HEADING}\n\nreason"
        self.assertTrue(looks_like_pass_stub_text(body, PASS_HEADINGS))

    def test_full_draft_is_not_pass_stub(self) -> None:
        self.assertFalse(
            looks_like_pass_stub_text("## 业务规则\n\n正文", PASS_HEADINGS)
        )

    def test_reads_file_head_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "stub.md"
            path.write_text(f"{NON_BUSINESS_HEADING}\n" + "x" * 9000, encoding="utf-8")
            self.assertTrue(looks_like_pass_stub_file(path, PASS_HEADINGS))

    def test_missing_file_is_not_pass_stub(self) -> None:
        self.assertFalse(looks_like_pass_stub_file(Path("/no/such/file.md"), PASS_HEADINGS))


class TestRulesOnlyPassRatio(unittest.TestCase):
    def test_zero_checked_returns_zero(self) -> None:
        self.assertEqual(rules_only_pass_ratio(3, 0), 0.0)

    def test_computes_ratio(self) -> None:
        self.assertEqual(rules_only_pass_ratio(2, 4), 0.5)


class TestEvaluateStrictViolations(unittest.TestCase):
    def test_all_pass_stubs_violation(self) -> None:
        msgs = evaluate_strict_violations(
            checked=5,
            full_files=0,
            missing_count=0,
            rules_with_only_pass=5,
            fail_if_all_pass_stubs=True,
            fail_if_any_pass_stub=False,
            fail_if_pass_stub_ratio_above=None,
            ratio=1.0,
        )
        self.assertEqual(len(msgs), 1)
        self.assertIn("Pass stubs", msgs[0])

    def test_ratio_violation(self) -> None:
        msgs = evaluate_strict_violations(
            checked=10,
            full_files=1,
            missing_count=0,
            rules_with_only_pass=9,
            fail_if_all_pass_stubs=False,
            fail_if_any_pass_stub=False,
            fail_if_pass_stub_ratio_above=0.5,
            ratio=0.9,
        )
        self.assertEqual(len(msgs), 1)
        self.assertIn("rules_only_pass_ratio", msgs[0])

    def test_skips_when_missing_files(self) -> None:
        msgs = evaluate_strict_violations(
            checked=5,
            full_files=0,
            missing_count=2,
            rules_with_only_pass=5,
            fail_if_all_pass_stubs=True,
            fail_if_any_pass_stub=True,
            fail_if_pass_stub_ratio_above=0.1,
            ratio=1.0,
        )
        self.assertEqual(msgs, [])


class TestClassifyKeywords(unittest.TestCase):
    def test_investigation_requires_word_boundary(self) -> None:
        from runtime.classify_keywords import contains_classify_keyword

        self.assertTrue(contains_classify_keyword("open investigation ticket", "investigation"))
        self.assertFalse(contains_classify_keyword("reinvestigation plan", "investigation"))

    def test_other_keywords_use_substring(self) -> None:
        from runtime.classify_keywords import contains_classify_keyword

        self.assertTrue(contains_classify_keyword("checkout flow", "checkout"))


if __name__ == "__main__":
    unittest.main()
