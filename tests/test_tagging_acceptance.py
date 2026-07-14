#!/usr/bin/env python3
"""Smoke tests for tagging_acceptance report helper."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.contract_support import ensure_scripts_on_path


class TestTaggingAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        ensure_scripts_on_path()

    def test_report_flags_zero_jira_and_writes_file(self) -> None:
        from distill import tagging_acceptance as ta

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            curated = root / "curated" / "by-root" / "999"
            mat = root / "materialized" / "by-root" / "999" / "facet-x"
            curated.mkdir(parents=True)
            mat.mkdir(parents=True)
            (mat / "a.md").write_text("# a\n", encoding="utf-8")
            (curated / "_materialization_closure.json").write_text(
                json.dumps({"facet-x/a.md": "_deliver/orders/orders-工作稿.md"}),
                encoding="utf-8",
            )
            (curated / "DOMAIN_MODULE_CHECKLIST.md").write_text(
                "\n".join(
                    [
                        "### Orders",
                        "- **Proposition slug**: `orders`",
                        "- **Status**: pending",
                        "- **Note**:",
                        "",
                        "### Autoship",
                        "- **Proposition slug**: `autoship-renewal`",
                        "- **Status**: pending",
                        "- **Note**:",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            with (
                patch.object(ta, "CURATED_BY_ROOT", root / "curated" / "by-root"),
                patch.object(ta, "MATERIALIZED_BY_ROOT", root / "materialized" / "by-root"),
                patch.object(ta, "REPO_ROOT", root),
            ):
                code = ta.report("999", after_s3=False)
            self.assertEqual(code, 0)
            out = curated / "TAGGING_ACCEPTANCE.md"
            self.assertTrue(out.is_file())
            text = out.read_text(encoding="utf-8")
            self.assertIn("INCOMPLETE", text)
            self.assertIn("autoship-renewal", text)
            self.assertIn("NO — keep pending", text)


if __name__ == "__main__":
    unittest.main()
