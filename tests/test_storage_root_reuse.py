#!/usr/bin/env python3
"""Unit tests for wiki/sync/storage_root reuse order (local first, then ancestors)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.contract_support import ensure_scripts_on_path

ensure_scripts_on_path()

from wiki.sync import storage_root as sr  # noqa: E402


class TestResolveStorageRootOrder(unittest.TestCase):
    def test_local_hit_skips_confluence_ancestors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pages = root / "domain-knowledge" / "extracted" / "by-root" / "100001" / "pages"
            pages.mkdir(parents=True)
            (pages / "555.md").write_text("# child\n", encoding="utf-8")

            with (
                patch.object(sr, "REPO_ROOT", root),
                patch.object(sr, "fetch_ancestor_ids") as fetch,
            ):
                chosen, reused = sr.resolve_storage_root_for_subtree(
                    "555", "https://example.atlassian.net/wiki", True
                )
            self.assertTrue(reused)
            self.assertEqual(chosen, "100001")
            fetch.assert_not_called()

    def test_local_miss_then_ancestor_hit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pages = root / "domain-knowledge" / "extracted" / "by-root" / "100001" / "pages"
            pages.mkdir(parents=True)
            (pages / "100001.md").write_text("# library root\n", encoding="utf-8")

            with (
                patch.object(sr, "REPO_ROOT", root),
                patch.dict(
                    "os.environ",
                    {"ATLASSIAN_EMAIL": "a@b.c", "ATLASSIAN_API_TOKEN": "tok"},
                    clear=False,
                ),
                patch.object(sr, "fetch_ancestor_ids", return_value=["100001", "99"]),
            ):
                chosen, reused = sr.resolve_storage_root_for_subtree(
                    "999999", "https://example.atlassian.net/wiki", True
                )
            self.assertTrue(reused)
            self.assertEqual(chosen, "100001")

    def test_reuse_disabled(self) -> None:
        chosen, reused = sr.resolve_storage_root_for_subtree(
            "555", "https://example.atlassian.net/wiki", False
        )
        self.assertFalse(reused)
        self.assertEqual(chosen, "555")


if __name__ == "__main__":
    unittest.main()
