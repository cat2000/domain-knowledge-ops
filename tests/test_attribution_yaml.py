#!/usr/bin/env python3
"""Unit tests for jira/lib/attribution_yaml.py."""

from __future__ import annotations

import unittest

from tests.contract_support import ensure_scripts_on_path

ensure_scripts_on_path()

from jira.lib.attribution_yaml import parse_attribution_yaml  # noqa: E402


class TestParseAttributionYaml(unittest.TestCase):
    def test_parses_scalars_and_list(self) -> None:
        text = "\n".join(
            [
                "key: DEV-1",
                "primary: checkout",
                "themes:",
                "  - checkout",
                "  - messaging",
                "product_line: demo",
                "distill_queue: true",
                "substance_tier: null",
            ]
        )
        record = parse_attribution_yaml(text)
        self.assertEqual(record["key"], "DEV-1")
        self.assertEqual(record["themes"], ["checkout", "messaging"])
        self.assertTrue(record["distill_queue"])
        self.assertIsNone(record["substance_tier"])


if __name__ == "__main__":
    unittest.main()
