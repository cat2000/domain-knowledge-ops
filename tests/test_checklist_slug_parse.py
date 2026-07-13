#!/usr/bin/env python3
"""Checklist slug parsing: field blocks (canonical) + legacy tables."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

from tests.contract_support import ensure_scripts_on_path

ensure_scripts_on_path()
distill_dir = Path(__file__).resolve().parents[1] / "scripts" / "distill"
if str(distill_dir) not in sys.path:
    sys.path.insert(0, str(distill_dir))

from proposition_extract import _confirmed_slugs, _has_pending_status  # noqa: E402


_CHECKLIST_TABLE = """\
| 主题 | 范围 | 物化目录 | 主入口 | 状态 | 备注 | 下一步 |
|------|------|----------|--------|------|------|--------|
| 商城（U智荟 / Mall APP）（mall-app） | scope | dirs | `_deliver/mall-app/mall-app-领域知识-工作稿.md` | 确认 |  | Compose |
| Reporting App（Hui）（hui-app） | scope | dirs | `_deliver/hui-app/hui-app-领域知识-工作稿.md` | 待确认 |  | S2 |
"""

_CHECKLIST_BLOCKS = """\
# 领域模块确认页

### 商城（U智荟 / Mall APP）
- **命题 slug**: `mall-app`
- **strategy 维度**: scope
- **领域子目录（扫描）**: dirs
- **主入口**: `_deliver/mall-app/mall-app-领域知识-工作稿.md`
- **状态**: 确认
- **术语备注**:
- **备注**: Compose

### Reporting App（Hui）
- **命题 slug**: `hui-app`
- **strategy 维度**: scope
- **领域子目录（扫描）**: dirs
- **主入口**: `_deliver/hui-app/hui-app-领域知识-工作稿.md`
- **状态**: 待确认
- **术语备注**:
- **备注**: S2
"""


class TestChecklistSlugParse(unittest.TestCase):
    def test_nested_parentheses_use_deliver_slug(self) -> None:
        slugs = _confirmed_slugs(_CHECKLIST_TABLE)
        self.assertEqual(slugs, [("mall-app", "商城（U智荟 / Mall APP）")])

    def test_pending_status_not_confirmed(self) -> None:
        self.assertTrue(_has_pending_status(_CHECKLIST_TABLE))

    def test_field_blocks_prefer_explicit_slug(self) -> None:
        slugs = _confirmed_slugs(_CHECKLIST_BLOCKS)
        self.assertEqual(slugs, [("mall-app", "商城（U智荟 / Mall APP）")])
        self.assertTrue(_has_pending_status(_CHECKLIST_BLOCKS))

    def test_shared_parser_rows(self) -> None:
        from runtime.checklist_modules import parse_checklist_rows

        rows = dict(parse_checklist_rows(_CHECKLIST_BLOCKS))
        self.assertEqual(rows["mall-app"], "确认")
        self.assertEqual(rows["hui-app"], "待确认")


if __name__ == "__main__":
    unittest.main()
