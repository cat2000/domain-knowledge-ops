"""Shared helpers for repository layout contract tests."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"


def repo_path(relative: str) -> Path:
    return REPO_ROOT / relative


def ensure_scripts_on_path() -> None:
    scripts = str(SCRIPTS_DIR)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)


def read_repo_text(relative: str) -> str:
    return repo_path(relative).read_text(encoding="utf-8")


def assert_paths_absent(case, relative_paths: tuple[str, ...], *, label: str = "path") -> None:
    for rel in relative_paths:
        with case.subTest(**{label: rel}):
            case.assertFalse(repo_path(rel).exists(), rel)


def assert_paths_are_files(case, relative_paths: tuple[str, ...], *, label: str = "path") -> None:
    for rel in relative_paths:
        with case.subTest(**{label: rel}):
            case.assertTrue(repo_path(rel).is_file(), rel)


def git_tracked_files(*relative_paths: str) -> list[str]:
    proc = subprocess.run(
        ["git", "ls-files", *relative_paths],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout)
    return [line for line in proc.stdout.splitlines() if line.strip()]


def assert_git_untracked(case, relative_paths: tuple[str, ...]) -> None:
    tracked = git_tracked_files(*relative_paths)
    case.assertEqual(tracked, [], tracked)


def assert_docs_exclude_tokens(
    case,
    doc_paths: tuple[str, ...],
    forbidden_tokens: tuple[str, ...],
) -> None:
    for rel in doc_paths:
        with case.subTest(doc=rel):
            case.assertTrue(repo_path(rel).is_file(), rel)
            body = read_repo_text(rel)
            for token in forbidden_tokens:
                case.assertNotIn(
                    token,
                    body,
                    f"{rel} must not reference legacy {token!r}",
                )


def run_script_help(relative_script: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(repo_path(relative_script)), "-h"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
