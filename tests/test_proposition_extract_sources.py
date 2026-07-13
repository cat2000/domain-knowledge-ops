#!/usr/bin/env python3
"""Unit tests for S3 source selection from S2 closure."""

from __future__ import annotations

import tempfile
import unittest
import sys
from pathlib import Path

from tests.contract_support import ensure_scripts_on_path

ensure_scripts_on_path()
distill_dir = Path(__file__).resolve().parents[1] / "scripts" / "distill"
if str(distill_dir) not in sys.path:
    sys.path.insert(0, str(distill_dir))

from distill.proposition_extract import _source_pages_for_slug  # noqa: E402


class TestSourcePagesForSlug(unittest.TestCase):
    def test_selects_confluence_materialized_pages_from_closure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            curated_root = root / "curated"
            rules_root = root / "materialized"
            mat = rules_root / "facet-checkout"
            mat.mkdir(parents=True)
            curated_root.mkdir()

            page = mat / "Checkout.md"
            page.write_text("# Checkout\n\nUser can pay.\n", encoding="utf-8")
            closure = {"facet-checkout/Checkout.md": "_deliver/checkout/checkout-领域知识-工作稿.md"}

            self.assertEqual(_source_pages_for_slug(curated_root, rules_root, closure, "checkout"), [page])

    def test_selects_jira_materialized_pages_from_closure_without_readmission(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            curated_root = root / "curated"
            rules_root = root / "materialized"
            mat = curated_root / "jira" / "materialized"
            mat.mkdir(parents=True)
            rules_root.mkdir()

            page = mat / "DEV-2.md"
            page.write_text("# DEV-2\n\nAC: user must pay.\n", encoding="utf-8")
            closure = {"jira/materialized/DEV-2.md": "_deliver/checkout/checkout-领域知识-工作稿.md"}

            self.assertEqual(_source_pages_for_slug(curated_root, rules_root, closure, "checkout"), [page])

    def test_does_not_fallback_to_facet_directory_without_s2_closure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            curated_root = root / "curated"
            rules_root = root / "materialized"
            mat = rules_root / "facet-checkout"
            mat.mkdir(parents=True)
            curated_root.mkdir()
            (mat / "Checkout.md").write_text("# Checkout\n\nUser can pay.\n", encoding="utf-8")

            self.assertEqual(_source_pages_for_slug(curated_root, rules_root, {}, "checkout"), [])


if __name__ == "__main__":
    unittest.main()
