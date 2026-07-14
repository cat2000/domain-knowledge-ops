#!/usr/bin/env python3
"""Tests for team-roots v2/v3 normalization."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from teams.team_roots_normalize import (
    libraries_for_team,
    library_key_for_root_id,
    load_normalized_team_roots,
    normalize_team_roots_doc,
    team_keys_for_library,
)


class TeamRootsNormalizeTest(unittest.TestCase):
    def test_v2_expands_to_library_per_team(self) -> None:
        raw = {
            "version": 2,
            "defaults": {"default_team": "demo"},
            "teams": {
                "demo": {
                    "root_id": "100001",
                    "confluence_overview": "https://example/wiki",
                    "deliver_by_proposition": {
                        "orders": ["orders", "orders-domain-brief.md"]
                    },
                    "jira": {"board_id": 1},
                }
            },
        }
        doc = normalize_team_roots_doc(raw)
        self.assertIn("demo", doc["libraries"])
        self.assertEqual(doc["libraries"]["demo"]["root_id"], "100001")
        self.assertEqual(doc["teams"]["demo"]["libraries"], ["demo"])
        self.assertEqual(doc["teams"]["demo"]["root_id"], "100001")
        self.assertEqual(
            doc["teams"]["demo"]["deliver_by_proposition"]["orders"][0], "orders"
        )

    def test_v3_multi_mount_merges_deliver_maps(self) -> None:
        raw = {
            "version": 3,
            "libraries": {
                "orders": {
                    "root_id": "200001",
                    "library_id": "200001",
                    "deliver_by_proposition": {
                        "ordering": ["ordering", "ordering-domain-brief.md"]
                    },
                },
                "payments": {
                    "root_id": "200002",
                    "library_id": "200002",
                    "deliver_by_proposition": {
                        "payments": ["payments", "payments-domain-brief.md"]
                    },
                },
            },
            "teams": {
                "web": {
                    "libraries": ["orders", "payments"],
                    "jira": {"board_id": 101},
                }
            },
        }
        doc = normalize_team_roots_doc(raw)
        team = doc["teams"]["web"]
        self.assertEqual(team["libraries"], ["orders", "payments"])
        self.assertEqual(team["root_id"], "200001")  # primary = first mount
        deliver = team["deliver_by_proposition"]
        self.assertIn("ordering", deliver)
        self.assertIn("payments", deliver)
        self.assertEqual(libraries_for_team(doc, "web"), ["orders", "payments"])
        self.assertEqual(library_key_for_root_id(doc, "200002"), "payments")
        self.assertEqual(team_keys_for_library(doc, "orders"), ["web"])

    def test_load_v3_example_file(self) -> None:
        example = (
            Path(__file__).resolve().parents[1]
            / "domain-knowledge/jira/team-roots.v3.example.json"
        )
        doc = load_normalized_team_roots(example)
        self.assertIn("demo", doc["teams"])
        self.assertIn("demo", doc["libraries"])
        self.assertEqual(doc["teams"]["demo"]["root_id"], "100001")
        self.assertEqual(doc["teams"]["orders-web"]["libraries"], ["orders", "payments"])
        self.assertIn("ordering", doc["teams"]["orders-web"]["deliver_by_proposition"])
        self.assertIn("payments", doc["teams"]["orders-web"]["deliver_by_proposition"])

    def test_shipped_team_roots_still_loads(self) -> None:
        path = (
            Path(__file__).resolve().parents[1]
            / "domain-knowledge/jira/team-roots.json"
        )
        doc = load_normalized_team_roots(path)
        self.assertIn("demo", doc["teams"])
        self.assertTrue(doc["teams"]["demo"].get("root_id"))


if __name__ == "__main__":
    unittest.main()
