#!/usr/bin/env python3
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


VALID_S6 = """# 示例-领域知识定稿

## 概述与范围
本文描述示例主题。

## 不在本文展开
- 工程材料不在本文展开。

## 领域模型摘要
- **一等业务对象**
  - 示例对象（Example Object）。
- **对象关系**
  - 示例对象承载展示规则。
- **状态机/状态转换**
  - 示例对象从待展示到已展示。

## 核心业务规则
### 示例规则
- **已确认规则**
  - 系统在满足条件时展示示例对象。
- **待确认边界**
  - 异常展示策略仍需确认。
- **用户可见影响**
  - 用户可以看到示例对象。
- **关联待确认事项**
  - 见 `数据与接口` 中字段来源待确认事项。

## 术语说明
- 示例对象（Example Object）：示例业务对象。

## 待确认事项
### 领域边界
- **影响规则**：示例规则
  - **待确认/待补充**：确认异常展示策略
  - **建议确认人**：示例产品负责人
  - **确认后影响**：可决定示例规则的例外处理。

### 规则冲突
- **影响规则**：示例规则
  - **待确认/待补充**：确认暂无规则冲突
  - **建议确认人**：示例产品负责人
  - **确认后影响**：可稳定示例规则。

### 数据与接口
- **影响规则**：示例规则
  - **待确认/待补充**：确认字段来源
  - **建议确认人**：数据负责人
  - **确认后影响**：可明确字段定义。

### 政策与展示
- **影响规则**：示例规则
  - **待确认/待补充**：确认展示文案
  - **建议确认人**：前端负责人
  - **确认后影响**：可明确展示说明。

### 待补充材料
- **影响规则**：示例规则
  - **待确认/待补充**：补充异常样例
  - **建议确认人**：示例产品负责人
  - **确认后影响**：可完善示例规则。

## 溯源
- 工作稿：`example.md`
"""


class TestReaderLanguagePolicy(unittest.TestCase):
    def test_policy_file_is_valid_and_loaded(self) -> None:
        from distill.s6_reader_quality_logic import DEFAULT_READER_LANGUAGE_POLICY, load_reader_language_policy

        checks, issues = load_reader_language_policy(DEFAULT_READER_LANGUAGE_POLICY)

        self.assertFalse(issues)
        self.assertGreaterEqual(len(checks), 3)
        self.assertTrue(all(check.id for check in checks))
        self.assertTrue(all(check.severity in {"error", "warn"} for check in checks))

    def test_policy_schema_reports_bad_regex(self) -> None:
        from distill.s6_reader_quality_logic import load_reader_language_policy

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "policy.json"
            path.write_text(
                '{"checks":[{"id":"bad","label":"Bad","severity":"error","patterns":["["]}]}',
                encoding="utf-8",
            )

            checks, issues = load_reader_language_policy(path)

        self.assertEqual(checks, [])
        self.assertTrue(any("invalid pattern" in issue for issue in issues))

    def test_reader_language_hits_are_policy_driven(self) -> None:
        from distill.s6_reader_quality_logic import ReaderLanguageCheck, reader_language_hits

        checks = [
            ReaderLanguageCheck(
                id="stage",
                label="流程阶段残留",
                severity="error",
                terms=("待裁决",),
                patterns=(),
            ),
            ReaderLanguageCheck(
                id="metaphor",
                label="过程表达",
                severity="warn",
                terms=("污染",),
                patterns=(),
            ),
        ]

        errors, warnings = reader_language_hits("这里仍待裁决，且会污染核心规则。", checks)

        self.assertEqual(errors, ["流程阶段残留: 待裁决"])
        self.assertEqual(warnings, ["过程表达: 污染"])


class TestS6ReaderQualityLogic(unittest.TestCase):
    def test_valid_layered_s6_text_passes(self) -> None:
        from distill.s6_reader_quality_logic import check_s6_text

        result = check_s6_text(VALID_S6, "example.md", reader_language_checks=[])

        self.assertEqual(result.issues, [])
        self.assertEqual(result.warnings, [])

    def test_flat_decision_card_is_rejected(self) -> None:
        from distill.s6_reader_quality_logic import check_s6_text

        text = VALID_S6.replace(
            "- **已确认规则**\n  - 系统在满足条件时展示示例对象。",
            "- 已确认规则：系统在满足条件时展示示例对象。",
        )

        result = check_s6_text(text, "example.md", reader_language_checks=[])

        self.assertTrue(any("labels not layered" in issue for issue in result.issues))

    def test_dense_confirmed_rule_bullet_is_rejected(self) -> None:
        from distill.s6_reader_quality_logic import check_s6_text

        text = VALID_S6.replace(
            "- **已确认规则**\n  - 系统在满足条件时展示示例对象。",
            "- **已确认规则**\n  - 示例对象包含分支一，满足条件时展示结果一；分支二满足条件时展示结果二。",
        )

        result = check_s6_text(text, "example.md", reader_language_checks=[])

        self.assertTrue(any("dense decision bullets" in issue for issue in result.issues))

    def test_delivery_context_in_core_rules_is_rejected(self) -> None:
        from distill.s6_reader_quality_logic import check_s6_text

        text = VALID_S6.replace(
            "- **已确认规则**\n  - 系统在满足条件时展示示例对象。",
            "- **已确认规则**\n  - 三方开发每周三发布体验版，并提供 bug list 供团队走查。",
        )

        result = check_s6_text(text, "example.md", reader_language_checks=[])

        self.assertTrue(any("delivery/collaboration material" in issue for issue in result.issues))

    def test_key_details_section_accepts_queryable_table(self) -> None:
        from distill.s6_reader_quality_logic import check_s6_text

        text = VALID_S6.replace(
            "## 术语说明",
            """## 关键明细
### 示例规则字段映射
| 字段 | 含义 |
|---|---|
| `status` | 示例对象展示状态 |

## 术语说明""",
        )

        result = check_s6_text(text, "example.md", reader_language_checks=[])

        self.assertEqual(result.issues, [])

    def test_key_details_section_rejects_unstructured_prose(self) -> None:
        from distill.s6_reader_quality_logic import check_s6_text

        text = VALID_S6.replace(
            "## 术语说明",
            """## 关键明细
这里会补充示例规则的相关字段。

## 术语说明""",
        )

        result = check_s6_text(text, "example.md", reader_language_checks=[])

        self.assertTrue(any("key details" in issue for issue in result.issues))

    def test_s5_structured_handoff_requires_key_details(self) -> None:
        from distill.s6_reader_quality_logic import check_s6_text

        result = check_s6_text(
            VALID_S6,
            "example.md",
            reader_language_checks=[],
            requires_key_details=True,
        )

        self.assertTrue(any("required by S5 structured detail handoff" in issue for issue in result.issues))


if __name__ == "__main__":
    unittest.main()
