from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


class TestStructuredSourceSignal(unittest.TestCase):
    def test_detects_long_mapping_table_shape(self) -> None:
        from distill.structured_source import structured_source_signal

        text = """
Title No.
Abbr.
Customer Title
Customer Type
APP显示中文title
升级至下一级职称需满足的条件
0
NONE
No Title
CPC
优惠顾客
联系客服可申请成为品牌合作伙伴
1
TBC
Temporary Business Center
DT
营养顾问
本周600CVP可升至高级品牌合作伙伴
2
NBC
Not Activated B/C
DS
营养顾问
本周600CVP可升至高级品牌合作伙伴
3
BC
Business Center
DT
营养顾问
本周600CVP可升至高级品牌合作伙伴
"""

        signal = structured_source_signal(text)

        self.assertTrue(signal["has_structured_source"])
        self.assertGreaterEqual(signal["business_header_hits"], 4)

    def test_short_formula_is_not_long_structured_source(self) -> None:
        from distill.structured_source import structured_source_signal

        text = """
已读率 = 已读数量 / 送达数量
送达数量 = 有效目标数 X 送达率
已读数量可以通过埋点数据来搜索
"""

        signal = structured_source_signal(text)

        self.assertFalse(signal["has_structured_source"])


if __name__ == "__main__":
    unittest.main()
