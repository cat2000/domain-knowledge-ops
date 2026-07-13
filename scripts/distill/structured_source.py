"""Detect structured source material that should be handed off as queryable details.

This module intentionally detects shape, not business meaning. It helps S3/S5
avoid losing long mapping tables whose individual rows may be too terse for
normal proposition extraction.
"""
from __future__ import annotations

import re


HEADER_TOKEN_RE = re.compile(
    r"("
    r"\b(?:no|number|abbr|type|status|condition|display|title|rank|field|path|service|comments?)\b|"
    r"编号|序号|缩写|类型|状态|条件|显示|职称|字段|路径|服务|备注|等级|阶段|目标|奖励|日期|时间窗|映射"
    r")",
    re.IGNORECASE,
)
VALUE_TOKEN_RE = re.compile(r"([A-Z]{2,}[A-Z0-9_]*|\d+(?:\.\d+)?|[\u4e00-\u9fff]{2,})")
MAPPING_CONNECTOR_RE = re.compile(r"(->|→|=>|:|：|=|对应|映射|显示为|变为|可升至|需满足)")
ENGINEERING_TABLE_NOISE_RE = re.compile(
    r"(eslint|prettier|editorconfig|javascript|typescript|lint|ast|plugin|"
    r"变量|缩进|分号|配置文件|代码风格|语法|插件|编辑器)",
    re.IGNORECASE,
)
BUSINESS_TABLE_HEADER_RE = re.compile(
    r"(title|customer|display|rank|status|condition|target|reward|field|"
    r"职称|用户|客户|显示|等级|状态|条件|目标|奖励|字段|映射|类型)",
    re.IGNORECASE,
)


def structured_source_signal(text: str) -> dict[str, object]:
    """Return source-shape signals for table-like or mapping-like material.

    The thresholds are deliberately about structural density:
    - enough repeated header-like tokens, and
    - enough compact value/mapping lines after extraction.
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    header_lines: list[str] = []
    value_lines: list[str] = []
    mapping_lines: list[str] = []

    for line in lines:
        if len(line) > 240:
            continue
        header_hits = HEADER_TOKEN_RE.findall(line)
        if header_hits:
            header_lines.append(line)
        value_hits = VALUE_TOKEN_RE.findall(line)
        if 2 <= len(value_hits) and len(line) <= 120:
            value_lines.append(line)
        if MAPPING_CONNECTOR_RE.search(line) and len(value_hits) >= 1:
            mapping_lines.append(line)

    unique_header_terms = {
        str(match).lower()
        for line in header_lines
        for match in HEADER_TOKEN_RE.findall(line)
        if str(match).strip()
    }
    business_header_hits = sum(1 for line in header_lines if BUSINESS_TABLE_HEADER_RE.search(line))
    engineering_noise_hits = len(ENGINEERING_TABLE_NOISE_RE.findall("\n".join(lines[:120])))
    has_signal = (
        len(unique_header_terms) >= 4 and len(value_lines) >= 16 and business_header_hits >= 2
    ) or (
        len(unique_header_terms) >= 3 and len(mapping_lines) >= 8 and business_header_hits >= 2
    ) or (
        len(unique_header_terms) >= 6 and business_header_hits >= 4 and len(lines) >= 20
    )
    if engineering_noise_hits >= 20:
        has_signal = False
    elif engineering_noise_hits >= 5 and business_header_hits < 4:
        has_signal = False

    return {
        "has_structured_source": has_signal,
        "header_terms": sorted(unique_header_terms)[:16],
        "header_line_count": len(header_lines),
        "value_line_count": len(value_lines),
        "mapping_line_count": len(mapping_lines),
        "business_header_hits": business_header_hits,
        "engineering_noise_hits": engineering_noise_hits,
        "sample_lines": value_lines[:8],
    }
