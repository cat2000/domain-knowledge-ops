#!/usr/bin/env python3
"""Unit tests for wiki/sync/pipeline_logic.py (no Confluence HTTP)."""

from __future__ import annotations

import unittest

from pathlib import Path

from tests.contract_support import ensure_scripts_on_path

ensure_scripts_on_path()

from wiki.sync.pipeline_logic import (  # noqa: E402
    apply_attachments_mode,
    build_auto_subtree_cql,
    build_enumerate_command,
    coerce_enum_page_size,
    default_enum_mode,
    extract_error_count,
    merge_descendants_inventory,
    s1_status_from_extract_report,
    merge_page_ids,
    orchestrator_extract_workers,
    product_tag_for_sync,
    read_json_rows,
    resolve_attachments_mode,
    resolve_fetch_attachments,
    resolve_reuse_enabled,
    should_enable_canonical_lift,
    write_json_artifact,
)
from wiki.sync.pipeline_types import SyncPaths  # noqa: E402


class TestDefaultEnumMode(unittest.TestCase):
    def test_defaults_to_cql(self) -> None:
        self.assertEqual(default_enum_mode(""), "cql")

    def test_accepts_bfs(self) -> None:
        self.assertEqual(default_enum_mode("bfs"), "bfs")


class TestCoerceEnumPageSize(unittest.TestCase):
    def test_cli_clamped(self) -> None:
        self.assertEqual(coerce_enum_page_size(999, ""), 250)
        self.assertEqual(coerce_enum_page_size(0, ""), 1)

    def test_env_fallback(self) -> None:
        self.assertEqual(coerce_enum_page_size(None, "100"), 100)


class TestMergePageIds(unittest.TestCase):
    def test_dedupes_and_appends(self) -> None:
        self.assertEqual(merge_page_ids("1,2", "2", "3"), "1,2,3")


class TestOrchestratorExtractWorkers(unittest.TestCase):
    def test_cli_wins(self) -> None:
        workers, src = orchestrator_extract_workers(4, 100, "", cpu_count=8)
        self.assertEqual(workers, 4)
        self.assertEqual(src, "--extract-workers")

    def test_auto_from_page_count(self) -> None:
        workers, src = orchestrator_extract_workers(None, 200, "", cpu_count=4)
        self.assertGreaterEqual(workers, 2)
        self.assertIn("enumerated pages", src)


class TestBuildAutoSubtreeCql(unittest.TestCase):
    def test_contains_space_and_root(self) -> None:
        cql = build_auto_subtree_cql("CMA", "48696506")
        self.assertIn('space = "CMA"', cql)
        self.assertIn("48696506", cql)
        self.assertIn("ancestor", cql)


class TestAttachmentsMode(unittest.TestCase):
    def test_default_off(self) -> None:
        self.assertEqual(resolve_attachments_mode(None, ""), "off")

    def test_env_tree(self) -> None:
        self.assertEqual(resolve_attachments_mode(None, "tree"), "tree")

    def test_apply_page_mode(self) -> None:
        pages, subroot = apply_attachments_mode("page", "12345", "", "")
        self.assertEqual(pages, "12345")
        self.assertEqual(subroot, "")

    def test_apply_tree_mode(self) -> None:
        pages, subroot = apply_attachments_mode("tree", "99", "1", "")
        self.assertEqual(subroot, "99")
        self.assertEqual(pages, "1")


class TestResolveFetchAttachments(unittest.TestCase):
    def test_cli_true(self) -> None:
        self.assertTrue(resolve_fetch_attachments(True, ""))

    def test_env_enables(self) -> None:
        self.assertTrue(resolve_fetch_attachments(False, "1"))

    def test_env_disables(self) -> None:
        self.assertFalse(resolve_fetch_attachments(True, "off"))


class TestProductTag(unittest.TestCase):
    def test_same_root(self) -> None:
        self.assertIn("root 48696506", product_tag_for_sync("48696506", "48696506"))

    def test_split_storage(self) -> None:
        tag = product_tag_for_sync("111", "222")
        self.assertIn("enum 111", tag)
        self.assertIn("storage 222", tag)


class TestMergeDescendantsInventory(unittest.TestCase):
    def test_no_merge_when_same_root(self) -> None:
        rows, merged = merge_descendants_inventory([], [{"id": "1"}], "9", "9")
        self.assertFalse(merged)
        self.assertEqual(rows, [{"id": "1"}])

    def test_merge_when_storage_differs(self) -> None:
        rows, merged = merge_descendants_inventory(
            [{"id": "1"}], [{"id": "2"}], "storage", "enum"
        )
        self.assertTrue(merged)
        self.assertEqual({row["id"] for row in rows}, {"1", "2"})


class TestResolveReuseEnabled(unittest.TestCase):
    def test_cli_opt_out(self) -> None:
        self.assertFalse(resolve_reuse_enabled(True, True, False))

    def test_space_overview_disables_reuse(self) -> None:
        self.assertFalse(resolve_reuse_enabled(False, True, True))


class TestCanonicalLift(unittest.TestCase):
    def test_enabled_with_ids(self) -> None:
        enabled, warn = should_enable_canonical_lift(True, False, ("1",))
        self.assertTrue(enabled)
        self.assertFalse(warn)

    def test_warn_when_ids_missing(self) -> None:
        enabled, warn = should_enable_canonical_lift(True, False, ())
        self.assertFalse(enabled)
        self.assertTrue(warn)


class TestBuildEnumerateCommand(unittest.TestCase):
    def test_cql_mode(self) -> None:
        cmd = build_enumerate_command(
            python="python3",
            script=Path("enumerate.py"),
            enum_page_size=100,
            subtree_json=Path("/tmp/sub.json"),
            enum_mode="cql",
            enum_root_id="1",
            cql_query="space = X",
        )
        self.assertIn("--cql", cmd)
        self.assertIn("space = X", cmd)

    def test_bfs_mode_uses_root(self) -> None:
        cmd = build_enumerate_command(
            python="python3",
            script=Path("enumerate.py"),
            enum_page_size=50,
            subtree_json=Path("/tmp/sub.json"),
            enum_mode="bfs",
            enum_root_id="48696506",
            cql_query=None,
        )
        self.assertIn("--root", cmd)
        self.assertIn("48696506", cmd)


class TestJsonArtifacts(unittest.TestCase):
    def test_write_and_read_rows(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rows.json"
            write_json_artifact(path, [{"id": "1"}])
            self.assertEqual(read_json_rows(path), [{"id": "1"}])
            write_json_artifact(path, [{"id": "2"}])
            self.assertEqual(read_json_rows(path), [{"id": "2"}])


class TestExtractReportStatus(unittest.TestCase):
    def test_complete_when_no_errors(self) -> None:
        report = {"error_count": 0}
        self.assertEqual(extract_error_count(report), 0)
        self.assertEqual(s1_status_from_extract_report(report), "complete")

    def test_partial_when_errors_present(self) -> None:
        report = {"error_count": 2}
        self.assertEqual(extract_error_count(report), 2)
        self.assertEqual(s1_status_from_extract_report(report), "partial")


class TestSyncPaths(unittest.TestCase):
    def test_for_storage_root_layout(self) -> None:
        paths = SyncPaths.for_storage_root(Path("/repo"), "123")
        self.assertEqual(paths.storage_root_id, "123")
        self.assertEqual(
            paths.descendants_full,
            Path("/repo/domain-knowledge/extracted/by-root/123/descendants-full.json"),
        )
        self.assertEqual(
            paths.rules_base,
            Path("/repo/domain-knowledge/materialized/by-root/123"),
        )


if __name__ == "__main__":
    unittest.main()
