#!/usr/bin/env python3
"""Tests for the dedicated S4 domain model quality gate."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

from tests.contract_support import ensure_scripts_on_path, repo_path


class TestDomainModelQuality(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        ensure_scripts_on_path()
        distill_dir = str(repo_path("scripts/distill"))
        if distill_dir not in sys.path:
            sys.path.insert(0, distill_dir)

    def test_accepts_layered_model_and_chain_binding(self) -> None:
        from distill import domain_model_quality

        issues = domain_model_quality.check_work_draft_text(_draft_path(), _good_draft())

        self.assertEqual(issues, [])

    def test_rejects_missing_domain_model_layers(self) -> None:
        from distill import domain_model_quality

        bad = _good_draft().replace("### 对象关系\n\n- Order carries payment.\n\n", "")

        issues = domain_model_quality.check_work_draft_text(_draft_path(), bad)

        self.assertTrue(any("domain model missing required dimensions" in issue for issue in issues))

    def test_rejects_chain_object_not_in_first_class_objects(self) -> None:
        from distill import domain_model_quality

        bad = _good_draft().replace("- 领域对象：Order\n", "- 领域对象：Invoice\n")

        issues = domain_model_quality.check_work_draft_text(_draft_path(), bad)

        self.assertTrue(any("not listed in domain model `一等业务对象`" in issue for issue in issues))

    def test_rejects_field_or_api_as_first_class_object(self) -> None:
        from distill import domain_model_quality

        bad = _good_draft().replace("- Order: customer checkout order.\n", "- `orderId` field: customer checkout order.\n")

        issues = domain_model_quality.check_work_draft_text(_draft_path(), bad)

        self.assertTrue(any("field/API/container-like" in issue for issue in issues))


def _draft_path() -> Path:
    return repo_path("domain-knowledge/curated/by-root/test-root/_deliver/checkout/checkout-领域知识-工作稿.md")


def _good_draft() -> str:
    return """# checkout · 领域知识工作稿（S5）

## 输入处置摘要

- `contract_candidate`: used in closed chain.
- `evidence_note`: reviewed and demoted when not rule-bearing.
- `noise_context`: excluded from business chains.
- 语义归一：duplicate checkout payment signals are merged into one rule.
- 顺序归一：source order is converted to business decision order.

## 领域模型

### 一等业务对象

- Order: customer checkout order.
- Payment: payment attempt for an order.

### 指标/字段

- `orderId`: order identifier.
- `paymentStatus`: payment state field.

### 展示容器

- Checkout page.
- Payment callback API.

### 对象关系

- Order carries payment.

### 状态机/状态转换

- Order unpaid -> paid after successful payment.

### 边界候选

- Release plan is support material.

## 组织顺序说明

- 链 1：Payment completion updates order state — payment outcome closes the order lifecycle.

## 已闭环决策链

### 链 1：Payment completion updates order state

- 领域对象：Order
- 状态变化：Order unpaid -> paid.
- 业务动作：store successful payment state.
- 展示容器/字段锚点：Checkout page; `paymentStatus`
- 适用对象：checkout customer.
- 触发条件：payment succeeds.
- 分支或动作：
  - Mark order as paid.
- 用户可见影响：
  - Customer can see payment success.
- 关联待裁决：无
- 证据来源：
  - Checkout Design

## 待裁决关键问题

当前未发现待裁决问题。
"""


if __name__ == "__main__":
    unittest.main()
