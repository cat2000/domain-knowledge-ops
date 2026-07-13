"""Shared rule phase classification for distill pipeline."""

from __future__ import annotations

import re
from collections.abc import Mapping

PHASE_ORDER = (
    "eligibility",
    "precheck",
    "adjudication",
    "settlement",
    "presentation",
    "placeholder",
)
PHASE_RANK = {name: idx for idx, name in enumerate(PHASE_ORDER)}

# Heading-first rules (more stable than body keyword hits).
_HEADING_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("placeholder", re.compile(r"(无正文来源页占位|no-text|待补录|无正文|白板|宏内容)", re.IGNORECASE)),
    ("precheck", re.compile(r"(前置|校验|会话|库存)", re.IGNORECASE)),
    ("settlement", re.compile(r"(结算|发放|入账|支付|回写)", re.IGNORECASE)),
    ("presentation", re.compile(r"(可见性|展示|列表|卡片|弹窗|发布窗口)", re.IGNORECASE)),
    ("adjudication", re.compile(r"(金额|促销|判定|状态机|规则链|计算)", re.IGNORECASE)),
    ("eligibility", re.compile(r"(资格判定|准入|报名|门槛|职称|onboarding|eligible|qualified)", re.IGNORECASE)),
]

# Text fallback rules for proposition lines / weak headings.
_TEXT_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("placeholder", re.compile(r"(no-text|待补录|无正文|白板|宏内容)", re.IGNORECASE)),
    ("precheck", re.compile(r"(会话|库存|校验|检查|前置|validate|session|cookie)", re.IGNORECASE)),
    ("settlement", re.compile(r"(结算|发放|入账|支付|回写|settle|payment)", re.IGNORECASE)),
    ("presentation", re.compile(r"(可见性|展示|列表|卡片|弹窗|文案|report|analytics|in_progress|finalized)", re.IGNORECASE)),
    ("adjudication", re.compile(r"(金额|促销|判定|计算|分支|状态机|threshold|上限|下限|阈值|规则)", re.IGNORECASE)),
    ("eligibility", re.compile(r"(资格|准入|报名|门槛|职称|eligible|qualified|onboarding)", re.IGNORECASE)),
]


def classify_rule_text(text: str) -> str:
    t = (text or "").strip()
    for phase, patt in _TEXT_RULES:
        if patt.search(t):
            return phase
    return "adjudication"


def classify_rule_block(
    *,
    heading: str,
    fields: Mapping[str, str] | None = None,
    body_text: str = "",
) -> str:
    h = (heading or "").strip()
    for phase, patt in _HEADING_RULES:
        if patt.search(h):
            return phase

    fields = fields or {}
    merged = " ".join(
        [
            h,
            fields.get("规则要点", ""),
            fields.get("条件", ""),
            fields.get("处理分支", ""),
            fields.get("用户可见后果", ""),
            body_text,
        ]
    ).strip()
    return classify_rule_text(merged)

