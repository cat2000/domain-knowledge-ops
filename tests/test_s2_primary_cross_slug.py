#!/usr/bin/env python3
"""Primary facet routing must still allow page-level cross-slug overrides."""

from __future__ import annotations

import tempfile
import unittest
import json
import sys
from pathlib import Path
from unittest.mock import patch

from tests.contract_support import ensure_scripts_on_path, repo_path
from tests.test_domain_profiles import MINIMAL_PROFILE


class TestS2PrimaryCrossSlug(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        ensure_scripts_on_path()
        distill_dir = str(repo_path("scripts/distill"))
        if distill_dir not in sys.path:
            sys.path.insert(0, distill_dir)

    def _install_fixture_profile(self):
        from runtime import domain_profiles

        tmp = tempfile.TemporaryDirectory()
        path = Path(tmp.name) / "s2-domain-profiles.json"
        path.write_text(json.dumps(MINIMAL_PROFILE), encoding="utf-8")
        domain_profiles.load_domain_profiles.cache_clear()
        patcher_path = patch.object(domain_profiles, "PROFILE_PATH", path)
        patcher_roots = patch.object(
            domain_profiles,
            "load_team_roots",
            return_value={
                "demo": {
                    "root_id": "100001",
                    "display_name": "Demo",
                    "s2_profile": "default",
                }
            },
        )
        patcher_path.start()
        patcher_roots.start()
        self.addCleanup(patcher_path.stop)
        self.addCleanup(patcher_roots.stop)
        self.addCleanup(domain_profiles.load_domain_profiles.cache_clear)
        self.addCleanup(tmp.cleanup)

    def test_primary_facet_page_title_can_override_to_better_slug(self) -> None:
        from distill import s2_recognize

        self._install_fixture_profile()
        s2_recognize._configure_profiles("100001")
        with tempfile.TemporaryDirectory() as tmp:
            mat_root = Path(tmp)
            facet = mat_root / "facet-checkout"
            facet.mkdir()
            (facet / "Forget-password-flow.md").write_text(
                "# Forget password flow\n\n"
                "### [Forget password](https://example.invalid/reset)\n\n"
                "User can reset password and recover account access.\n",
                encoding="utf-8",
            )
            (facet / "Shopping-cart-release-plan.md").write_text(
                "# Shopping cart release plan\n\n"
                "购物车为空的显示。购物车不为空时显示商品、收货地址和支付入口。\n",
                encoding="utf-8",
            )

            rows = s2_recognize._build_machine_decisions(mat_root, rescue_threshold=2)

        by_file = {row.materialized_file: row for row in rows}
        identity_row = by_file["facet-checkout/Forget-password-flow.md"]
        cart_row = by_file["facet-checkout/Shopping-cart-release-plan.md"]

        self.assertEqual(identity_row.proposed_slug, "compliance-identity")
        self.assertEqual(identity_row.decision_mode, "rescued")
        self.assertIn("primary facet cross-slug", identity_row.reason)

        self.assertEqual(cart_row.proposed_slug, "checkout")
        self.assertEqual(cart_row.decision_mode, "primary")

    def test_confluence_manifest_drives_source_registry(self) -> None:
        from distill import s2_recognize

        self._install_fixture_profile()
        s2_recognize._configure_profiles("100001")
        with tempfile.TemporaryDirectory() as tmp:
            mat_root = Path(tmp)
            facet = mat_root / "facet-checkout"
            ignored = mat_root / "facet-messaging"
            facet.mkdir()
            ignored.mkdir()
            (mat_root / "_materialized_manifest.json").write_text(
                json.dumps(
                    {
                        "targets": [
                            {"path": "facet-checkout/Shopping-cart-release-plan.md"}
                        ]
                    }
                ),
                encoding="utf-8",
            )
            (facet / "Shopping-cart-release-plan.md").write_text(
                "# Shopping cart release plan\n\n购物车结账支付规则。\n",
                encoding="utf-8",
            )
            (ignored / "Notification.md").write_text(
                "# Notification\n\npush notification\n",
                encoding="utf-8",
            )

            rows = s2_recognize._build_machine_decisions(mat_root, rescue_threshold=2)

        self.assertEqual([row.materialized_file for row in rows], ["facet-checkout/Shopping-cart-release-plan.md"])

    def test_jira_attribution_enters_unified_recognize(self) -> None:
        from distill import s2_recognize

        self._install_fixture_profile()
        s2_recognize._configure_profiles("100001")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mat_root = root / "materialized"
            curated_root = root / "curated"
            attr = curated_root / "jira" / "attribution"
            jira_mat = curated_root / "jira" / "materialized"
            mat_root.mkdir()
            attr.mkdir(parents=True)
            jira_mat.mkdir(parents=True)
            (attr / "DEV-1.yaml").write_text(
                "\n".join(
                    [
                        "key: DEV-1",
                        "primary: checkout",
                        "themes:",
                        "  - checkout",
                        "confidence: medium",
                        "distill_tier: proposition_core",
                        "proposition_id: cart_checkout",
                        "proposition_extract: true",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (jira_mat / "DEV-1.md").write_text("# DEV-1\n\nAC: checkout payment result is visible.\n", encoding="utf-8")

            rows = s2_recognize._build_machine_decisions(mat_root, rescue_threshold=2, curated_root=curated_root)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].materialized_file, "jira/materialized/DEV-1.md")
        self.assertEqual(rows[0].source_facet, "jira:checkout")
        self.assertEqual(rows[0].proposed_slug, "checkout")
        self.assertEqual(rows[0].decision_mode, "primary")
        self.assertIn("jira attribution route", rows[0].reason)

    def test_jira_index_only_goes_to_appendix(self) -> None:
        from distill import s2_recognize

        self._install_fixture_profile()
        s2_recognize._configure_profiles("100001")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mat_root = root / "materialized"
            curated_root = root / "curated"
            attr = curated_root / "jira" / "attribution"
            attr.mkdir(parents=True)
            mat_root.mkdir()
            (attr / "DEV-2.yaml").write_text(
                "\n".join(
                    [
                        "key: DEV-2",
                        "primary: checkout",
                        "themes:",
                        "  - checkout",
                        "confidence: medium",
                        "distill_tier: index_only",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            rows = s2_recognize._build_machine_decisions(mat_root, rescue_threshold=2, curated_root=curated_root)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].decision_mode, "appendix")
        self.assertIsNone(rows[0].proposed_slug)

    def test_s3_writes_cross_slug_handoff_for_auditable_transfer(self) -> None:
        from distill import proposition_extract

        with tempfile.TemporaryDirectory() as tmp:
            curated_root = Path(tmp) / "100001"
            curated_root.mkdir()
            closure = {
                "facet-checkout/Forget-password-flow.md": (
                    "_deliver/compliance-identity/compliance-identity-领域知识-工作稿.md"
                )
            }
            decisions = [
                {
                    "materialized_file": "facet-checkout/Forget-password-flow.md",
                    "source_facet": "facet-checkout",
                    "decision_mode": "rescued",
                    "proposed_slug": "compliance-identity",
                    "confidence": "high",
                    "score": 101,
                    "reason": (
                        "primary facet cross-slug override "
                        "(checkout -> compliance-identity): identity/auth reset rule"
                    ),
                }
            ]

            proposition_extract._write_cross_slug_handoff(curated_root, closure, decisions)

            payload = json.loads(
                (curated_root / "_aggregate" / "CROSS_SLUG_HANDOFF.json").read_text(encoding="utf-8")
            )
            md = (curated_root / "_aggregate" / "CROSS_SLUG_HANDOFF.md").read_text(encoding="utf-8")

        self.assertEqual(payload["cross_slug_total"], 1)
        self.assertEqual(payload["entries"][0]["target_slug"], "compliance-identity")
        self.assertIn("Forget-password-flow.md", md)


if __name__ == "__main__":
    unittest.main()
