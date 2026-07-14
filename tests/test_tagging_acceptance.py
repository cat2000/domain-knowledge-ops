#!/usr/bin/env python3
"""Smoke tests for tagging_acceptance report helper."""

from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from tests.contract_support import ensure_scripts_on_path


class TestTaggingAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        ensure_scripts_on_path()

    @contextmanager
    def _patched(self, ta, root: Path):
        with (
            patch.object(ta, "CURATED_BY_ROOT", root / "curated" / "by-root"),
            patch.object(ta, "MATERIALIZED_BY_ROOT", root / "materialized" / "by-root"),
            patch.object(ta, "REPO_ROOT", root),
        ):
            yield

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

            with self._patched(ta, root):
                code = ta.report(
                    "999", after_s3=False, after_s7=False, strict=False
                )
            self.assertEqual(code, 0)
            out = curated / "TAGGING_ACCEPTANCE.md"
            self.assertTrue(out.is_file())
            text = out.read_text(encoding="utf-8")
            self.assertIn("INCOMPLETE", text)
            self.assertIn("autoship-renewal", text)
            self.assertIn("NO — keep pending", text)
            self.assertIn("Axis landing", text)
            self.assertIn("industry adjudication axes", text)
            self.assertNotIn("Mall catalog", text)

    def test_after_s7_fails_zero_rule_fake_coverage(self) -> None:
        from distill import tagging_acceptance as ta

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            curated = root / "curated" / "by-root" / "999"
            deliver = curated / "_deliver" / "orders"
            agg = curated / "_aggregate" / "orders"
            mat = root / "materialized" / "by-root" / "999" / "facet-x"
            for d in (deliver, agg, mat):
                d.mkdir(parents=True)
            (mat / "a.md").write_text("# a\n", encoding="utf-8")
            (curated / "_materialization_closure.json").write_text(
                json.dumps(
                    {
                        "facet-x/a.md": "_deliver/orders/orders-工作稿.md",
                        "facet-x/b.md": "_deliver/orders/orders-工作稿.md",
                        "facet-x/c.md": "_deliver/orders/orders-工作稿.md",
                    }
                ),
                encoding="utf-8",
            )
            (curated / "DOMAIN_MODULE_CHECKLIST.md").write_text(
                "\n".join(
                    [
                        "### Orders",
                        "- **Proposition slug**: `orders`",
                        "- **Status**: confirmed",
                        "- **Note**:",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            (agg / "orders-propositions.json").write_text(
                json.dumps({"pages_total": 12, "pages_with_props": 10}),
                encoding="utf-8",
            )
            (deliver / "orders-domain-brief.md").write_text(
                "# Orders\n\n## Core business rules\n\n(none)\n",
                encoding="utf-8",
            )

            with self._patched(ta, root):
                code = ta.report(
                    "999", after_s3=False, after_s7=True, strict=True
                )
            self.assertEqual(code, 1)
            text = (curated / "TAGGING_ACCEPTANCE.md").read_text(encoding="utf-8")
            self.assertIn("fake coverage", text)
            self.assertIn("Post-S7 write-through", text)
            self.assertIn("Gate failures", text)

    def test_after_s7_ok_with_rules(self) -> None:
        from distill import tagging_acceptance as ta

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            curated = root / "curated" / "by-root" / "999"
            deliver = curated / "_deliver" / "orders"
            agg = curated / "_aggregate" / "orders"
            mat = root / "materialized" / "by-root" / "999" / "facet-x"
            for d in (deliver, agg, mat):
                d.mkdir(parents=True)
            (mat / "a.md").write_text("# a\n", encoding="utf-8")
            (curated / "_materialization_closure.json").write_text(
                json.dumps(
                    {
                        "facet-x/a.md": "_deliver/orders/orders-工作稿.md",
                        "facet-x/b.md": "_deliver/orders/orders-工作稿.md",
                        "facet-x/c.md": "_deliver/orders/orders-工作稿.md",
                    }
                ),
                encoding="utf-8",
            )
            (curated / "DOMAIN_MODULE_CHECKLIST.md").write_text(
                "\n".join(
                    [
                        "### Orders",
                        "- **Proposition slug**: `orders`",
                        "- **Status**: confirmed",
                        "- **Note**:",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            (agg / "orders-propositions.json").write_text(
                json.dumps({"pages_total": 5, "pages_with_props": 4}),
                encoding="utf-8",
            )
            (deliver / "orders-domain-brief.md").write_text(
                "\n".join(
                    [
                        "# Orders",
                        "",
                        "### Rule 1 — Checkout hold",
                        "- When pending pay, hold promo.",
                        "",
                        "### Rule 2 — Cart limit",
                        "- Max line items apply.",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            with self._patched(ta, root):
                code = ta.report(
                    "999", after_s3=True, after_s7=True, strict=True
                )
            self.assertEqual(code, 0)
            text = (curated / "TAGGING_ACCEPTANCE.md").read_text(encoding="utf-8")
            self.assertIn("| `orders` |", text)
            self.assertNotIn("Gate failures", text)


if __name__ == "__main__":
    unittest.main()
