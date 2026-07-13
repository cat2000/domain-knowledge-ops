#!/usr/bin/env python3
"""Unit tests for wiki/lib/attachment_logic.py (no Confluence HTTP)."""

from __future__ import annotations

import unittest

from tests.contract_support import ensure_scripts_on_path

ensure_scripts_on_path()

from wiki.lib.attachment_logic import (  # noqa: E402
    attachment_download_url,
    discover_filenames_from_body_markup,
    extract_bytes,
    merge_synthetic_attachments,
    resolve_handler_id,
    safe_ext,
    user_handler_map_path,
)


class TestSafeExt(unittest.TestCase):
    def test_lowercase_extension(self) -> None:
        self.assertEqual(safe_ext("docs/Report.PDF"), ".pdf")

    def test_no_extension(self) -> None:
        self.assertEqual(safe_ext("README"), "")


class TestResolveHandlerId(unittest.TestCase):
    def test_builtin_csv(self) -> None:
        self.assertEqual(resolve_handler_id(".csv", {}), "csv_utf8")

    def test_user_map_overrides(self) -> None:
        self.assertEqual(resolve_handler_id(".csv", {".csv": "text_plain"}), "text_plain")


class TestUserHandlerMapPath(unittest.TestCase):
    def test_under_scripts_wiki(self) -> None:
        from pathlib import Path

        path = user_handler_map_path(Path("/repo"))
        self.assertEqual(path, Path("/repo/scripts/wiki/confluence_attachment_handler_map.json"))


class TestExtractBytes(unittest.TestCase):
    def test_text_plain_utf8(self) -> None:
        text, status, detail = extract_bytes("text_plain", "你好\n".encode())
        self.assertEqual(status, "ok")
        self.assertIn("你好", text)
        self.assertTrue(detail)

    def test_skip_handler(self) -> None:
        text, status, detail = extract_bytes("skip", b"data")
        self.assertEqual(status, "skipped")
        self.assertEqual(text, "")
        self.assertEqual(detail, "handler_skip")

    def test_unknown_handler(self) -> None:
        _, status, detail = extract_bytes("no_such_handler", b"x")
        self.assertEqual(status, "unsupported")
        self.assertIn("unknown_handler", detail)


class TestDiscoverFilenamesFromBodyMarkup(unittest.TestCase):
    def test_ri_filename_attribute(self) -> None:
        html = '<ri:attachment ri:filename="diagram.png" />'
        names = discover_filenames_from_body_markup(html, "", "12345")
        self.assertEqual(names, ["diagram.png"])

    def test_download_url_same_page_only(self) -> None:
        storage = '/download/attachments/99/other.png /download/attachments/12345/keep.jpg'
        names = discover_filenames_from_body_markup("", storage, "12345")
        self.assertEqual(names, ["keep.jpg"])


class TestAttachmentDownloadUrl(unittest.TestCase):
    def test_absolute_download_link(self) -> None:
        att = {"_links": {"download": "https://x.atlassian.net/wiki/download/a/b"}}
        url = attachment_download_url("https://x.atlassian.net/wiki", "1", att)
        self.assertEqual(url, "https://x.atlassian.net/wiki/download/a/b")

    def test_relative_wiki_path(self) -> None:
        att = {"_links": {"download": "/wiki/download/attachments/1/file.pdf"}}
        url = attachment_download_url("https://x.atlassian.net/wiki", "1", att)
        self.assertEqual(url, "https://x.atlassian.net/wiki/download/attachments/1/file.pdf")

    def test_fallback_from_title(self) -> None:
        att = {"title": "my doc.pdf", "_links": {}}
        url = attachment_download_url("https://x.atlassian.net/wiki", "42", att)
        self.assertIn("/download/attachments/42/", url)
        self.assertIn("my%20doc.pdf", url)


class TestMergeSyntheticAttachments(unittest.TestCase):
    def test_adds_body_only_filenames(self) -> None:
        meta = [{"title": "known.txt", "_links": {}}]
        merged = merge_synthetic_attachments(
            meta,
            "1",
            '<ri:attachment ri:filename="extra.png" />',
            "",
        )
        titles = {a["title"] for a in merged}
        self.assertEqual(titles, {"known.txt", "extra.png"})


if __name__ == "__main__":
    unittest.main()
