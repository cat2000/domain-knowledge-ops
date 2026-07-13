#!/usr/bin/env python3
"""Tests for the dedicated S5 work draft quality gate."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

from tests.contract_support import ensure_scripts_on_path, repo_path


class TestS5WorkDraftQuality(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        ensure_scripts_on_path()
        distill_dir = str(repo_path("scripts/distill"))
        if distill_dir not in sys.path:
            sys.path.insert(0, distill_dir)

    def test_accepts_complete_work_draft_contract(self) -> None:
        from distill import s5_work_draft_quality

        issues = s5_work_draft_quality.check_work_draft_text(_draft_path(), _good_draft())

        self.assertEqual(issues, [])

    def test_rejects_missing_closed_chain_field(self) -> None:
        from distill import s5_work_draft_quality

        bad = _good_draft().replace("- 适用对象：Shopper\n", "")

        issues = s5_work_draft_quality.check_work_draft_text(_draft_path(), bad)

        self.assertTrue(any("closed chain 1 missing required fields" in issue for issue in issues), issues)

    def test_rejects_unresolved_token_inside_closed_chain(self) -> None:
        from distill import s5_work_draft_quality

        bad = _good_draft().replace("- 状态变化：valid account -> login success\n", "- 状态变化：待确认\n")

        issues = s5_work_draft_quality.check_work_draft_text(_draft_path(), bad)

        self.assertTrue(any("unresolved tokens appear inside closed section" in issue for issue in issues), issues)

    def test_rejects_unreciprocated_pending_issue_reference(self) -> None:
        from distill import s5_work_draft_quality

        bad = _good_draft().replace("- 关联链：链 1\n", "- 关联链：链 2\n")

        issues = s5_work_draft_quality.check_work_draft_text(_draft_path(), bad)

        self.assertTrue(any("references issue 1, but the issue binds chains" in issue for issue in issues), issues)

    def test_rejects_structured_detail_without_queryable_shape(self) -> None:
        from distill import s5_work_draft_quality

        bad = _good_draft().replace(
            "| 项 | 条件/字段/状态 | 业务含义 | 例外/待确认 | 来源 |\n"
            "|---|---|---|---|---|\n"
            "| `status` | account state | login basis | none | Example source |\n",
            "This paragraph is not queryable enough.\n",
        )

        issues = s5_work_draft_quality.check_work_draft_text(_draft_path(), bad)

        self.assertTrue(any("must use a table or layered list" in issue for issue in issues), issues)


def _draft_path() -> Path:
    return repo_path("domain-knowledge/curated/by-root/test-root/_deliver/shopper/shopper-领域知识-工作稿.md")


def _good_draft() -> str:
    return """# shopper · 领域知识工作稿（S5）

## 概述与范围

This S5 work draft covers shopper access rules.

## 输入处置摘要

- `contract_candidate`: enters closed chain.
- `evidence_note`: high-value evidence is uplifted or deferred.
- `noise_context`: delivery noise is excluded.
- 语义归一：duplicate login signals are merged.
- 来源/顺序归一：source order is converted to business decision order.

## 领域模型

### 一等业务对象

- Shopper account: user identity that controls access.

### 指标/字段

- `status`: account state.

### 展示容器

- Login page.

### 对象关系

- Shopper account controls login page access.

### 状态机/状态转换

- valid account -> login success.

### 边界候选

- Delivery notes.

## 组织顺序说明

- 链 1：Shopper access — identity comes first.

## 已闭环决策链

### 链 1：Shopper access

- 领域对象：Shopper account
- 状态变化：valid account -> login success
- 业务动作：authenticate shopper account.
- 展示容器/字段锚点：Login page; `status`
- 适用对象：Shopper
- 触发条件：User submits valid credentials.
- 分支或动作：
  - Valid account can log in.
- 用户可见影响：
  - User enters the shopping surface.
- 关联待裁决：问题 1
- 证据来源：
  - Example source.

## 待裁决关键问题

### 问题 1：Password failure handling

- 关联链：链 1
- 待裁决点：confirm exact failure message.
- 当前证据：source does not expose failure copy.
- 待确认事项：provide product copy.
- 建议确认人：product owner.
- 决策影响：changes visible login failure wording.

## 结构化明细转交

### Account status fields（完整展开）

| 项 | 条件/字段/状态 | 业务含义 | 例外/待确认 | 来源 |
|---|---|---|---|---|
| `status` | account state | login basis | none | Example source |

## 溯源

- Example source.
"""


if __name__ == "__main__":
    unittest.main()
