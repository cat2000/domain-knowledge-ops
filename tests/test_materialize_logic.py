#!/usr/bin/env python3
"""Unit tests for wiki/lib/materialize_logic.py."""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tests.contract_support import ensure_scripts_on_path

ensure_scripts_on_path()

from wiki.lib.materialize_logic import (  # noqa: E402
    is_skip_outline,
    parse_frontmatter,
    safe_rules_path,
    strip_extract_heading,
)
from wiki.steps.materialize_run import MANIFEST_FILE, materialize_dirs  # noqa: E402


class TestIsSkipOutline(unittest.TestCase):
    def test_dash_and_em_dash(self) -> None:
        self.assertTrue(is_skip_outline("—"))
        self.assertTrue(is_skip_outline(""))
        self.assertFalse(is_skip_outline("checkout/foo.md"))


class TestParseFrontmatter(unittest.TestCase):
    def test_splits_yaml_and_body(self) -> None:
        raw = '---\ntitle: "Hello"\nkb_outline: x.md\n---\n\nBody text'
        front_matter, body = parse_frontmatter(raw)
        self.assertEqual(front_matter["title"], "Hello")
        self.assertEqual(front_matter["kb_outline"], "x.md")
        self.assertEqual(body.strip(), "Body text")


class TestSafeRulesPath(unittest.TestCase):
    def test_resolves_under_base(self) -> None:
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            out = safe_rules_path(base, "foo/bar.md")
            self.assertEqual(out, (base / "foo/bar.md").resolve())

    def test_rejects_traversal(self) -> None:
        with TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                safe_rules_path(Path(tmp), "../escape.md")


class TestStripExtractHeading(unittest.TestCase):
    def test_removes_rest_heading(self) -> None:
        body = "## 正文（Confluence REST 提取）\n\nHello"
        self.assertEqual(strip_extract_heading(body), "Hello")


class TestMaterializeDirs(unittest.TestCase):
    def test_writes_manifest_and_removes_stale_md(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            extracted = root / "pages"
            rules = root / "materialized"
            extracted.mkdir()
            (rules / "facet-old").mkdir(parents=True)
            (rules / "facet-old" / "stale.md").write_text("old", encoding="utf-8")
            (extracted / "1.md").write_text(
                "\n".join(
                    [
                        "---",
                        'title: "Checkout"',
                        "page_id: 1",
                        'web_ui: "https://wiki/1"',
                        'kb_outline: "facet-checkout/checkout.md"',
                        "---",
                        "",
                        "## 正文（Confluence REST 提取）",
                        "",
                        "Body",
                    ]
                ),
                encoding="utf-8",
            )

            files_written, pages_skipped = materialize_dirs(extracted, rules)

            self.assertEqual(files_written, 1)
            self.assertEqual(pages_skipped, 0)
            self.assertTrue((rules / "facet-checkout" / "checkout.md").is_file())
            self.assertFalse((rules / "facet-old" / "stale.md").exists())
            manifest = (rules / MANIFEST_FILE).read_text(encoding="utf-8")
            self.assertIn('"path": "facet-checkout/checkout.md"', manifest)
            self.assertIn('"stale_deleted": 1', manifest)


if __name__ == "__main__":
    unittest.main()
