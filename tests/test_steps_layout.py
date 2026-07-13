#!/usr/bin/env python3
"""Layout: step *_run / *_types must live under <pipeline>/steps/."""

from __future__ import annotations

import unittest
from pathlib import Path

from tests.contract_support import REPO_ROOT
from tests.domain_knowledge_contracts import (
    FORBIDDEN_STEP_RUN_OUTSIDE_STEPS,
    REQUIRED_STEP_RUN_FILES,
)


class TestStepRunPlacement(unittest.TestCase):
    def test_required_step_run_files_exist(self) -> None:
        for rel in REQUIRED_STEP_RUN_FILES:
            with self.subTest(path=rel):
                self.assertTrue((REPO_ROOT / rel).is_file(), rel)

    def test_step_run_not_at_pipeline_root(self) -> None:
        for rel in FORBIDDEN_STEP_RUN_OUTSIDE_STEPS:
            with self.subTest(path=rel):
                self.assertFalse((REPO_ROOT / rel).exists(), f"{rel} must not exist")


if __name__ == "__main__":
    unittest.main()
