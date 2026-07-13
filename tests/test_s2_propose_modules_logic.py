#!/usr/bin/env python3
"""Unit tests for s2_propose_modules_logic.py."""

from __future__ import annotations

import unittest

from tests.contract_support import ensure_scripts_on_path

ensure_scripts_on_path()

from distill.s2_propose_modules_logic import (  # noqa: E402
    PageRecord,
    assign_pages_to_seeds,
    build_parent_map_bfs,
    load_page_records,
    parse_module_seeds,
    propose_modules,
    slugify_label,
    wiki_branch_for_page,
)
from distill.s2_propose_modules_logic import load_seeds_config  # noqa: E402


class TestSlugify(unittest.TestCase):
    def test_strips_numeric_prefix(self) -> None:
        self.assertEqual(slugify_label("02-Scrum 工作方式"), "scrum")

    def test_ascii_fallback(self) -> None:
        slug = slugify_label("中文标题")
        self.assertTrue(slug.startswith("section-"))
        self.assertEqual(len(slug), len("section-") + 8)

    def test_ascii_label_keeps_readable_slug(self) -> None:
        self.assertEqual(slugify_label("Reporting App"), "reporting-app")


class TestWikiBranch(unittest.TestCase):
    def test_direct_child_branch(self) -> None:
        parent = {"100": None, "200": "100", "201": "200"}
        titles = {"100": "Root", "200": "Hui Section"}
        self.assertEqual(wiki_branch_for_page("201", "100", parent, titles), "Hui Section")


class TestParentMapBfs(unittest.TestCase):
    def test_builds_parent_links(self) -> None:
        children = {
            "1": [{"id": "2", "title": "Branch A"}, {"id": "3", "title": "Leaf"}],
            "2": [{"id": "4", "title": "Deep"}],
        }

        def iter_children(pid: str):
            return children.get(pid, [])

        parent_by_child, children_by_parent, titles = build_parent_map_bfs(
            root_id="1",
            iter_children=iter_children,
        )
        self.assertEqual(parent_by_child["4"], "2")
        self.assertEqual(wiki_branch_for_page("4", "1", parent_by_child, titles), "Branch A")
        self.assertIn("2", children_by_parent["1"])


class TestProposeModules(unittest.TestCase):
    def test_shipped_shell_has_empty_module_seeds(self) -> None:
        cfg = load_seeds_config()
        self.assertEqual(cfg.get("module_seeds") or [], [])
        self.assertEqual(parse_module_seeds(cfg, team="demo"), [])
        self.assertTrue(cfg.get("strategy_dimensions"))

    def test_inline_seeds_score_checkout_pages(self) -> None:
        cfg = {
            "module_seeds": [
                {
                    "teams": ["demo"],
                    "slug": "checkout",
                    "name_cn": "Checkout",
                    "axis": "orders",
                    "strategy_dimension_ids": ["eligibility-branch-outcome"],
                    "keywords": ["checkout", "cart", "结账"],
                    "facet_hints": ["facet-checkout"],
                }
            ]
        }
        seeds = parse_module_seeds(cfg, team="demo")
        pages = [
            PageRecord("1", "Checkout Design", "DEMO", "", facet_dir="facet-checkout"),
            PageRecord("2", "Sprint Review 2024", "DEMO", "", facet_dir="facet-unmatched"),
        ]
        by_seed = assign_pages_to_seeds(pages, seeds)
        self.assertEqual(len(by_seed.get("checkout") or []), 1)

    def test_team_scoped_seeds(self) -> None:
        cfg = {
            "module_seeds": [
                {
                    "teams": ["demo"],
                    "slug": "checkout",
                    "name_cn": "Checkout",
                    "axis": "x",
                    "keywords": ["checkout"],
                    "facet_hints": [],
                },
                {
                    "teams": ["other"],
                    "slug": "other-mod",
                    "name_cn": "Other",
                    "axis": "y",
                    "keywords": ["other"],
                    "facet_hints": [],
                },
            ]
        }
        demo_seeds = {s.slug for s in parse_module_seeds(cfg, team="demo")}
        other = {s.slug for s in parse_module_seeds(cfg, team="other")}
        self.assertEqual(demo_seeds, {"checkout"})
        self.assertEqual(other, {"other-mod"})

    def test_propose_payload_shape_with_inline_seeds(self) -> None:
        from unittest.mock import patch

        pages = [
            PageRecord("1", "Checkout API", "DEMO", "", facet_dir="facet-checkout"),
            PageRecord("2", "CBP Bonus", "DEMO", "", facet_dir="facet-compensation-cbp"),
        ]
        cfg = {
            "strategy_dimensions": [],
            "module_seeds": [
                {
                    "teams": ["demo"],
                    "slug": "checkout",
                    "name_cn": "Checkout",
                    "axis": "x",
                    "keywords": ["checkout", "cart"],
                    "facet_hints": ["facet-checkout"],
                },
                {
                    "teams": ["demo"],
                    "slug": "compensation-cbp",
                    "name_cn": "Comp",
                    "axis": "y",
                    "keywords": ["bonus", "cbp"],
                    "facet_hints": ["facet-compensation-cbp"],
                },
            ],
        }
        with patch("distill.s2_propose_modules_logic.load_seeds_config", return_value=cfg):
            payload = propose_modules(
                root_id="100001",
                pages=pages,
                parent_by_child=None,
                title_by_id=None,
                team_key="demo",
            )
        self.assertEqual(payload["page_total"], 2)
        slugs = {m["slug"] for m in payload["proposed_modules"]}
        self.assertIn("checkout", slugs)
        self.assertIn("compensation-cbp", slugs)


class TestLoadPageRecords(unittest.TestCase):
    def test_reads_descendants_rows(self) -> None:
        rows = [{"id": "42", "title": "Contest List", "spaceKey": "CMA", "webUi": "https://x"}]
        recs = load_page_records(rows, __import__("pathlib").Path("/nonexistent"))
        self.assertEqual(recs[0].page_id, "42")
        self.assertEqual(recs[0].title, "Contest List")


if __name__ == "__main__":
    unittest.main()
