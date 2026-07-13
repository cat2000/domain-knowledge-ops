#!/usr/bin/env python3
"""Contract tests for Beck-style intention-revealing names in scripts/."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from tests.contract_support import REPO_ROOT, ensure_scripts_on_path
from tests.domain_knowledge_contracts import (
    ACTIVE_SCRIPTS_DIR,
    FORBIDDEN_ACTIVE_SCRIPT_LINE_PATTERNS,
    FORBIDDEN_ACTIVE_SCRIPT_SYMBOLS,
    FORBIDDEN_SHORT_LOCAL_SNIPPETS,
)


def iter_active_script_files() -> list[Path]:
    root = REPO_ROOT / ACTIVE_SCRIPTS_DIR
    return sorted(
        p
        for p in root.rglob("*.py")
        if "archive" not in p.parts and p.is_file()
    )


class TestActiveScriptNaming(unittest.TestCase):
    def test_no_forbidden_line_patterns(self) -> None:
        for path in iter_active_script_files():
            rel = path.relative_to(REPO_ROOT)
            text = path.read_text(encoding="utf-8")
            for line_no, line in enumerate(text.splitlines(), start=1):
                for pattern, message in FORBIDDEN_ACTIVE_SCRIPT_LINE_PATTERNS:
                    with self.subTest(path=str(rel), line=line_no, pattern=pattern):
                        self.assertIsNone(
                            re.search(pattern, line),
                            f"{rel}:{line_no}: {message}\n  {line!r}",
                        )

    def test_no_forbidden_symbols(self) -> None:
        for path in iter_active_script_files():
            rel = path.relative_to(REPO_ROOT)
            text = path.read_text(encoding="utf-8")
            for symbol in FORBIDDEN_ACTIVE_SCRIPT_SYMBOLS:
                with self.subTest(path=str(rel), symbol=symbol):
                    self.assertNotIn(
                        symbol,
                        text,
                        f"{rel} must not reference {symbol!r}",
                    )

    def test_no_short_local_snippets(self) -> None:
        for rel, snippet in FORBIDDEN_SHORT_LOCAL_SNIPPETS:
            path = REPO_ROOT / ACTIVE_SCRIPTS_DIR / rel
            with self.subTest(path=rel, snippet=snippet):
                self.assertTrue(path.is_file(), rel)
                text = path.read_text(encoding="utf-8")
                self.assertNotIn(snippet, text, f"{rel} still has {snippet!r}")


class TestCanonicalSymbols(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        ensure_scripts_on_path()

    def test_confluence_extract_page_attachments(self) -> None:
        from wiki.lib import confluence_attachment_extract

        self.assertTrue(
            callable(getattr(confluence_attachment_extract, "extract_page_attachments", None))
        )

    def test_wiki_sync_env_uses_runtime_paths(self) -> None:
        from runtime.paths import REPO_ROOT as runtime_repo
        from wiki.sync import env

        self.assertEqual(env.REPO_ROOT, runtime_repo)


if __name__ == "__main__":
    unittest.main()
