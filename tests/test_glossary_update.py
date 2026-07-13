#!/usr/bin/env python3
"""Glossary update should be generated from S6 final drafts, not used as S2 source."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.distill.glossary_update import (
    AUTO_SECTION_HEADING,
    extract_terms_from_final_draft,
    render_auto_glossary_section,
    update_glossary_text,
)


class TestGlossaryUpdate(unittest.TestCase):
    def test_extract_terms_from_s6_terms_section(self) -> None:
        text = """# 示例-领域知识定稿

## 核心业务规则
- 正文。

## 术语说明
- 里程碑（Milestone）：新人周期目标与奖励对象。
- CVP：奖励和目标计算中的分值单位。
- `API`：系统接口缩写。

## 待确认事项
- 后续。
"""
        terms = extract_terms_from_final_draft(text, Path("_deliver/demo/示例-领域知识定稿.md"))
        self.assertEqual([term.name for term in terms], ["里程碑（Milestone）", "CVP", "API"])
        self.assertEqual(terms[0].definition, "新人周期目标与奖励对象。")

    def test_update_glossary_replaces_root_auto_block(self) -> None:
        existing = """# 术语表（Ubiquitous Language）

## 手工术语

### 已有术语

- **定义**：保留。

## 自动沉淀术语（S6 定稿）

<!-- BEGIN AUTO-GLOSSARY: root=old -->
### 旧术语
- **定义**：旧。
<!-- END AUTO-GLOSSARY: root=old -->
"""
        section = render_auto_glossary_section(
            "100001",
            [
                extract_terms_from_final_draft(
                    "## 术语说明\n- CVP：奖励和目标计算中的分值单位。\n",
                    Path("_deliver/cbp/定稿.md"),
                )[0]
            ],
        )
        updated = update_glossary_text(existing, "100001", section)

        self.assertIn(AUTO_SECTION_HEADING, updated)
        self.assertIn("<!-- BEGIN AUTO-GLOSSARY: root=old -->", updated)
        self.assertIn("<!-- BEGIN AUTO-GLOSSARY: root=100001 -->", updated)
        self.assertIn("### CVP", updated)

    def test_update_glossary_file_from_temp_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            deliver = root / "curated/by-root/1/_deliver/demo"
            deliver.mkdir(parents=True)
            (deliver / "示例-领域知识定稿.md").write_text(
                "## 术语说明\n- 里程碑（Milestone）：新人周期目标与奖励对象。\n",
                encoding="utf-8",
            )
            glossary = root / "language/glossary.md"
            glossary.parent.mkdir(parents=True)
            glossary.write_text("# 术语表\n", encoding="utf-8")

            from scripts.distill.glossary_update import update_glossary_file

            changed = update_glossary_file(
                root_id="1",
                curated_by_root=root / "curated/by-root",
                glossary_path=glossary,
            )
            self.assertTrue(changed)
            self.assertIn("### 里程碑（Milestone）", glossary.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
