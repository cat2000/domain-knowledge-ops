#!/usr/bin/env python3
from __future__ import annotations

import unittest
from pathlib import Path

from tests.contract_support import ensure_scripts_on_path


REPO = Path(__file__).resolve().parents[1]


VALID_LAYERED_S5 = """# example · 领域知识工作稿（S4/S5）

## 概述与范围

This S5 draft keeps source language but exposes the required domain structure.

## 输入处置摘要

- `contract_candidate`:
  - Enters closed chain.
- `evidence_note`:
  - High-value evidence is uplifted into closed chain or structured detail.
- `noise_context`:
  - Delivery-only material is excluded.
- Semantic normalization:
  - Pages and fields are demoted to anchors instead of domain objects.
- Source / order normalization:
  - Source order is reorganized into business decision order.

## 领域模型

### 一等业务对象

- **Shopper account**
  - Controls access and visible actions.

### 指标/字段

- `status`: account state.

### 展示容器

- Login page.

### 对象关系

- Shopper account controls login page visibility.

### 状态机/状态转换

- Shopper account valid -> login success.

### 边界候选

- Delivery process notes.

## 组织顺序说明

- 链 1：Shopper access — identity comes first.

## 已闭环决策链

### 链 1：Shopper access

- 领域对象：Shopper account
- 状态变化：valid account -> login success
- 业务动作：Authenticate shopper account
- 展示容器/字段锚点：Login page; `status`
- 适用对象：Shopper
- 触发条件：User submits valid credentials
- 分支或动作：
  - Valid account can log in.
- 用户可见影响：
  - User enters the shopping surface.
- 证据来源：
  - Example source.

## 待裁决关键问题

## 溯源

- Example source.
"""


class TestDistillQualityLogic(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        ensure_scripts_on_path()

    def test_layered_domain_model_and_source_language_disposition_pass(self) -> None:
        from distill.quality import _s4_structure_violations

        md = (
            REPO
            / "domain-knowledge/curated/by-root/example/_deliver/example/example-领域知识-工作稿.md"
        )

        issues = _s4_structure_violations(md, VALID_LAYERED_S5)

        self.assertFalse(
            [
                issue
                for issue in issues
                if "missing semantic normalization" in issue
                or "missing source/order normalization" in issue
                or "not listed in domain model" in issue
            ],
            issues,
        )


if __name__ == "__main__":
    unittest.main()
