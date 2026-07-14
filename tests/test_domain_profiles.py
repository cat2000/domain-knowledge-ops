#!/usr/bin/env python3
"""Domain profile selection must be scoped by team/root when configured."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.contract_support import ensure_scripts_on_path


MINIMAL_PROFILE = {
    "checklist_themes": [
        {"slug": "checkout", "name_cn": "结账与下单", "axis": "交易流程与结算规则"},
        {"slug": "messaging", "name_cn": "消息与触达", "axis": "通知规则"},
        {"slug": "compliance-identity", "name_cn": "合规与身份", "axis": "身份边界"},
    ],
    "s1_facets": [],
    "s1_noise": {"min_title_chars": 2, "exact_titles": ["Test"], "title_prefixes": []},
    "s2": {
        "primary_facet_to_slug": {"facet-checkout": "checkout"},
        "domain_cues": {
            "checkout": ["checkout", "cart", "payment", "结账", "购物车"],
            "compliance-identity": ["password", "identity", "密码"],
            "messaging": ["notification", "push", "通知"],
        },
        "business_signals": ["必须", "if", "when", "显示"],
        "strong_cues": ["checkout", "cart", "password"],
        "engineering_noise": ["meeting minutes", "sprint review"],
        "hard_non_business_path": [],
        "explicit_non_business_path": [],
        "route_overrides": [
            {
                "pattern": "(forget password|reset password|密码重置|忘记密码)",
                "slug": "compliance-identity",
                "reason": "identity/auth reset rule",
            }
        ],
    },
}


class TestDomainProfiles(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        ensure_scripts_on_path()

    def test_shipped_shell_has_empty_checklist_themes(self) -> None:
        from runtime.domain_profiles import load_checklist_themes, load_domain_profiles

        raw = load_domain_profiles()
        self.assertEqual(raw.get("checklist_themes") or [], [])
        self.assertEqual(load_checklist_themes("100001"), [])
        self.assertEqual(load_checklist_themes("demo"), [])

    def test_require_checklist_themes_errors_when_empty(self) -> None:
        from runtime.domain_profiles import require_checklist_themes

        with self.assertRaises(ValueError) as ctx:
            require_checklist_themes("100001")
        msg = str(ctx.exception)
        self.assertIn("strategy.md", msg)
        self.assertIn("setup-domain-ops", msg)

    def test_s1_noise_rules_are_profile_data(self) -> None:
        from runtime.domain_profiles import load_s1_noise_rules

        rules = load_s1_noise_rules()
        self.assertEqual(rules["min_title_chars"], 2)
        self.assertIn("Test", rules["exact_titles"])

    def test_fixture_profile_loads_themes(self) -> None:
        from runtime import domain_profiles

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "s2-domain-profiles.json"
            path.write_text(json.dumps(MINIMAL_PROFILE), encoding="utf-8")
            with patch.object(domain_profiles, "PROFILE_PATH", path):
                domain_profiles.load_domain_profiles.cache_clear()
                try:
                    with patch.object(
                        domain_profiles,
                        "load_team_roots",
                        return_value={
                            "demo": {
                                "root_id": "100001",
                                "display_name": "Demo",
                                "s2_profile": "default",
                            }
                        },
                    ):
                        from runtime.domain_profiles import load_checklist_themes, load_s2_profiles, require_checklist_themes

                        slugs = [s for s, _, _ in require_checklist_themes("100001")]
                        self.assertIn("checkout", slugs)
                        self.assertIn("messaging", slugs)
                        profile = load_s2_profiles("100001")
                        self.assertEqual(profile["primary_facet_to_slug"]["facet-checkout"], "checkout")
                        self.assertEqual(
                            [s for s, _, _ in load_checklist_themes("demo")],
                            [s for s, _, _ in load_checklist_themes("100001")],
                        )
                finally:
                    domain_profiles.load_domain_profiles.cache_clear()

    def test_known_team_without_profile_or_explicit_default_fails(self) -> None:
        from runtime import domain_profiles

        with patch.object(
            domain_profiles,
            "load_team_roots",
            return_value={
                "newteam": {
                    "root_id": "999999",
                    "display_name": "New Team",
                }
            },
        ):
            with self.assertRaisesRegex(ValueError, "missing S2 domain profile"):
                domain_profiles.load_checklist_themes("999999")

    def test_unknown_scoped_root_fails_instead_of_using_default(self) -> None:
        from runtime.domain_profiles import load_checklist_themes

        with self.assertRaisesRegex(ValueError, "unknown S2 profile scope"):
            load_checklist_themes("000000")

    def test_explicit_default_s2_profile_allowed_even_when_empty(self) -> None:
        from runtime import domain_profiles

        with patch.object(
            domain_profiles,
            "load_team_roots",
            return_value={
                "newteam": {
                    "root_id": "999999",
                    "display_name": "New Team",
                    "s2_profile": "default",
                }
            },
        ):
            # Shipped shell: default profile is empty themes (strategy-first)
            self.assertEqual(domain_profiles.load_checklist_themes("999999"), [])

    def test_v3_library_root_id_resolves_to_mounting_team(self) -> None:
        from runtime import domain_profiles

        with tempfile.TemporaryDirectory() as tmp:
            roots = Path(tmp) / "team-roots.json"
            roots.write_text(
                json.dumps(
                    {
                        "version": 3,
                        "defaults": {"deliverable_locale": "en", "default_team": "cma"},
                        "libraries": {
                            "cma": {
                                "root_id": "48693262",
                                "library_id": "48693262",
                                "s2_profile": "default",
                            }
                        },
                        "teams": {
                            "cma": {
                                "libraries": ["cma"],
                                "display_name": "CMA",
                                "s2_profile": "default",
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            with patch.object(domain_profiles, "TEAM_ROOTS_PATH", roots):
                domain_profiles.load_team_roots.cache_clear()
                try:
                    self.assertEqual(
                        domain_profiles.team_key_for_scope("48693262"), "cma"
                    )
                    self.assertEqual(
                        domain_profiles.load_checklist_themes("48693262"), []
                    )
                finally:
                    domain_profiles.load_team_roots.cache_clear()


if __name__ == "__main__":
    unittest.main()
