#!/usr/bin/env python3
"""domain-knowledge methodology SSOT is English; Chinese ships as *.zh-CN.md."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DK = REPO / "domain-knowledge"
CJK = re.compile(r"[\u4e00-\u9fff]")

EN_SSOT = (
    "strategy.md",
    "strategy.example.md",
    "distill-quality-bar.md",
    "distill-authoring-contract.md",
    "distill-document-skeleton.md",
    "DOMAIN_MODULE_CHECKLIST.template.md",
    "jira/README.md",
    "jira/first-principles-attribution.md",
    "jira/pipeline-design.md",
)

# These core SSOT docs must be fully CJK-free (count == 0)
ZERO_CJK_DOCS = (
    "distill-authoring-contract.md",
    "distill-quality-bar.md",
    "distill-document-skeleton.md",
    "DOMAIN_MODULE_CHECKLIST.template.md",
    "strategy.md",
    "jira/README.md",
    "jira/first-principles-attribution.md",
    "jira/pipeline-design.md",
)

CURSOR_ZERO_CJK = (
    REPO / ".cursor/contracts/domain-knowledge-pipeline-contract.md",
    REPO / ".cursor/contracts/jira-issue-domain-knowledge-context.md",
    REPO / ".cursor/rules/domain-module-checklist.mdc",
    REPO / ".cursor/rules/jira_classify.mdc",
    REPO / ".cursor/rules/requirement_risk.md",
    REPO / ".cursor/rules/ticket_system.md",
    REPO / ".cursor/rules/ticket_splitter_principles.md",
    REPO / ".cursor/skills/generate-knowledge-from-wiki/RUNBOOK.md",
    REPO / ".cursor/skills/add-knowledge-from-jira/RUNBOOK.md",
)

CURSOR_ZH_LOCALES = (
    REPO / ".cursor/contracts/domain-knowledge-pipeline-contract.zh-CN.md",
    REPO / ".cursor/contracts/jira-issue-domain-knowledge-context.zh-CN.md",
    REPO / ".cursor/rules/domain-module-checklist.zh-CN.md",
    REPO / ".cursor/rules/jira_classify.zh-CN.md",
    REPO / ".cursor/rules/requirement_risk.zh-CN.md",
    REPO / ".cursor/rules/ticket_system.zh-CN.md",
    REPO / ".cursor/rules/ticket_splitter_principles.zh-CN.md",
)


def _cjk_letter_share(text: str) -> float:
    letters = re.findall(r"[A-Za-z\u4e00-\u9fff]", text)
    if not letters:
        return 0.0
    return len(CJK.findall(text)) / len(letters)


class TestDomainKnowledgeEnglishSsot(unittest.TestCase):
    def test_zh_cn_locales_exist(self) -> None:
        for name in EN_SSOT:
            zh = DK / name.replace(".md", ".zh-CN.md")
            self.assertTrue(zh.is_file(), zh)

    def test_english_ssot_is_mostly_english(self) -> None:
        for name in EN_SSOT:
            path = DK / name
            text = path.read_text(encoding="utf-8")
            self.assertIn("Chinese locale:", text, name)
            share = _cjk_letter_share(text)
            self.assertLess(
                share,
                0.02,
                f"{name} CJK letter share {share:.1%} too high for EN SSOT",
            )

    def test_zero_cjk_in_core_ssot_docs(self) -> None:
        for name in ZERO_CJK_DOCS:
            path = DK / name
            if not path.is_file():
                self.skipTest(f"{name} not found")
            text = path.read_text(encoding="utf-8")
            count = len(CJK.findall(text))
            self.assertEqual(
                count,
                0,
                f"{name} contains {count} CJK characters; samples: "
                f"{sorted(set(CJK.findall(text)))[:10]}",
            )

    def test_zh_cn_locales_remain_chinese_heavy(self) -> None:
        for name in (
            "strategy.zh-CN.md",
            "distill-quality-bar.zh-CN.md",
            "jira/first-principles-attribution.zh-CN.md",
            "jira/pipeline-design.zh-CN.md",
        ):
            share = _cjk_letter_share((DK / name).read_text(encoding="utf-8"))
            self.assertGreater(share, 0.20, name)

    def test_cursor_en_ssot_zero_cjk(self) -> None:
        for path in CURSOR_ZERO_CJK:
            text = path.read_text(encoding="utf-8")
            count = len(CJK.findall(text))
            self.assertEqual(
                count,
                0,
                f"{path} contains {count} CJK characters",
            )

    def test_cursor_zh_cn_locales_exist(self) -> None:
        for path in CURSOR_ZH_LOCALES:
            self.assertTrue(path.is_file(), path)
            share = _cjk_letter_share(path.read_text(encoding="utf-8"))
            self.assertGreater(share, 0.08, path.name)


if __name__ == "__main__":
    unittest.main()
