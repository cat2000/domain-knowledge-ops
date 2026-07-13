#!/usr/bin/env python3
"""
Regression tests for scripts layout refactors (P0–P4).

Run from repo root:
  python3 -m unittest discover -s tests -p 'test_*.py' -v

No network / ATLASSIAN_* required unless noted.
"""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"

# Shipped demo team from domain-knowledge/jira/team-roots.json
TEAM_ROOTS = {"demo": "100001"}

CLI_HELP_SCRIPTS = [
    "sync_domain_knowledge_from_confluence.py",
    "wiki/steps/extract.py",
    "wiki/steps/enumerate.py",
    "wiki/steps/source_coverage.py",
    "domain_check.py",
    "run_distill_gate.py",
    "run_jira_knowledge.py",
    "jira/steps/fetch.py",
    "run_jira_ingest.py",
    "distill/coverage.py",
    "distill/glossary_update.py",
    "distill/s6_reader_quality.py",
    "jira/steps/check_pipeline.py",
]


def _scripts_on_path() -> None:
    s = str(SCRIPTS)
    if s not in sys.path:
        sys.path.insert(0, s)


class TestRepoLayout(unittest.TestCase):
    def test_wiki_package_exists(self) -> None:
        self.assertTrue((SCRIPTS / "wiki" / "sync" / "pipeline.py").is_file())
        self.assertTrue((SCRIPTS / "wiki" / "lib" / "facet_classify.py").is_file())

    def test_jira_teams_packages(self) -> None:
        self.assertTrue((SCRIPTS / "jira" / "lib" / "jira_team_config.py").is_file())
        self.assertTrue((SCRIPTS / "teams" / "registry.py").is_file())

    def test_distill_package_exists(self) -> None:
        self.assertTrue((SCRIPTS / "distill" / "coverage.py").is_file())
        self.assertTrue((SCRIPTS / "distill" / "quality.py").is_file())
        self.assertTrue((SCRIPTS / "distill" / "domain_layout.py").is_file())

    def test_pipeline_steps_packages(self) -> None:
        self.assertTrue((SCRIPTS / "wiki" / "steps" / "enumerate.py").is_file())
        self.assertTrue((SCRIPTS / "wiki" / "steps" / "extract.py").is_file())
        self.assertTrue((SCRIPTS / "jira" / "run.py").is_file())
        self.assertTrue((SCRIPTS / "jira" / "steps" / "fetch.py").is_file())
        self.assertTrue((SCRIPTS / "ARCHITECTURE.md").is_file())

    def test_runtime_ssot_modules(self) -> None:
        for rel in (
            "runtime/paths.py",
            "runtime/domain_knowledge_paths.py",
            "runtime/classify_keywords.py",
            "runtime/atlassian_env.py",
        ):
            self.assertTrue((SCRIPTS / rel).is_file(), rel)

    def test_classify_module_on_disk(self) -> None:
        p = SCRIPTS / "wiki" / "lib" / "facet_classify.py"
        self.assertTrue(p.is_file())
        self.assertFalse((SCRIPTS / "wiki" / "imports").exists())


class TestCanonicalImports(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _scripts_on_path()

    def test_wiki_sync_env_repo(self) -> None:
        from runtime.paths import REPO_ROOT as runtime_repo
        from wiki.sync.env import REPO_ROOT as impl_repo

        self.assertEqual(impl_repo, runtime_repo)
        self.assertEqual(impl_repo, REPO)

    def test_sync_env_classify_path(self) -> None:
        from wiki.sync.env import FACET_CLASSIFY_MODULE

        self.assertTrue(FACET_CLASSIFY_MODULE.is_file())
        self.assertIn("wiki/lib", str(FACET_CLASSIFY_MODULE))

    def test_wiki_s1_main_importable(self) -> None:
        from wiki.sync.pipeline import main

        self.assertTrue(callable(main))

    def test_jira_step_mains_match_package(self) -> None:
        from jira import run as impl_jira
        from jira.steps import fetch as impl_fetch
        import run_jira_knowledge as entry_jira

        self.assertIs(entry_jira.main, impl_jira.main)
        from jira.steps.fetch import main as fetch_main

        self.assertTrue(callable(fetch_main))

    def test_distill_gate_modules_expose_main(self) -> None:
        from distill import coverage, domain_layout, glossary_update, quality, s6_reader_quality

        for mod in (coverage, quality, domain_layout, s6_reader_quality, glossary_update):
            self.assertTrue(callable(mod.main), mod.__name__)

    def test_run_distill_gate_updates_glossary_after_domain_check(self) -> None:
        text = (SCRIPTS / "distill/gate.py").read_text(encoding="utf-8")
        self.assertIn("domain_check.py", text)
        self.assertIn("distill/glossary_update.py", text)

    def test_auto_extract_workers(self) -> None:
        from wiki.steps.extract import auto_extract_workers

        self.assertEqual(auto_extract_workers(1), 1)
        w = auto_extract_workers(200)
        self.assertGreaterEqual(w, 2)
        self.assertLessEqual(w, 16)


class TestTeamRegistry(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _scripts_on_path()

    def test_resolve_all_teams(self) -> None:
        from teams.registry import resolve_team

        for team, root_id in TEAM_ROOTS.items():
            key, cfg = resolve_team(team)
            self.assertEqual(key, team)
            self.assertEqual(str(cfg["root_id"]), root_id)

    def test_resolve_team_by_board_id(self) -> None:
        from teams.registry import resolve_team

        key, cfg = resolve_team("1")
        self.assertEqual(key, "demo")
        self.assertEqual(cfg["jira"]["board_id"], 1)

    def test_team_roots_json_loads(self) -> None:
        from teams.registry import load_team_roots

        teams = load_team_roots()
        self.assertEqual(set(teams), {"demo"})
        self.assertEqual(str(teams["demo"]["root_id"]), "100001")


class TestDomainClassify(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _scripts_on_path()

    def test_classify_returns_theme_and_outline(self) -> None:
        from wiki.lib.facet_classify import classify

        theme, kb = classify("Checkout payment flow", "wechat pay notify shop")
        self.assertIsInstance(theme, str)
        self.assertTrue(theme)
        self.assertIsInstance(kb, str)


class TestCliHelp(unittest.TestCase):
    def test_cli_help_exit_zero(self) -> None:
        for script in CLI_HELP_SCRIPTS:
            with self.subTest(script=script):
                proc = subprocess.run(
                    [sys.executable, str(SCRIPTS / script), "-h"],
                    cwd=str(REPO),
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(
                    proc.returncode,
                    0,
                    f"{script} -h failed: {proc.stderr[:400]}",
                )

    def test_domain_check_subcommands_help(self) -> None:
        for cmd in ("distill", "jira", "all"):
            with self.subTest(cmd=cmd):
                proc = subprocess.run(
                    [sys.executable, str(SCRIPTS / "domain_check.py"), cmd, "-h"],
                    cwd=str(REPO),
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(proc.returncode, 0, proc.stderr[:300])


class TestKbCheckFacade(unittest.TestCase):
    def test_run_pipeline_delegates_domain_check(self) -> None:
        text = (SCRIPTS / "jira/run_pipeline.py").read_text(encoding="utf-8")
        self.assertIn("domain_check.py", text)
        self.assertIn('"jira"', text)

    def test_domain_check_distill_invokes_coverage(self) -> None:
        """Facade must delegate; use --warn-only so data gaps do not fail the run."""
        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "domain_check.py"),
                "distill",
                "--root-id",
                TEAM_ROOTS["demo"],
                "--warn-only",
            ],
            cwd=str(REPO),
            capture_output=True,
            text=True,
            timeout=120,
        )
        combined = proc.stdout + proc.stderr
        self.assertIn("distill/coverage.py", combined)
        self.assertIn("+", combined, "expected delegated command echo on stderr")
        self.assertEqual(proc.returncode, 0, combined[:800])


class TestPyCompileAllScripts(unittest.TestCase):
    def test_compile_scripts_tree(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "compileall",
                "-q",
                str(SCRIPTS / "wiki"),
                str(SCRIPTS / "jira"),
                str(SCRIPTS / "teams"),
                str(SCRIPTS / "distill"),
                str(SCRIPTS / "runtime"),
                str(SCRIPTS / "wiki" / "steps"),
                str(SCRIPTS / "jira" / "steps"),
            ]
            + [str(SCRIPTS / n) for n in CLI_HELP_SCRIPTS if (SCRIPTS / n).is_file()],
            cwd=str(REPO),
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
