"""
Ticket text substance scoring (no LLM).

Used by attribution (distill_queue) and coverage scripts.
"""

from __future__ import annotations

import re
from typing import Any, Mapping

# AC / 规则类描述特征（中英）
_RULE_LIKE = re.compile(
    r"当.+则|须|必须|不得|should|must|展示|规则：|发放条件|用户.*可|"
    r"if .+ then|验收|acceptance|模块[一二三四]|步骤|scenario",
    re.I,
)

_VERIFIED_ONLY = re.compile(r"^verified on stage", re.I)


def text_blob(raw: Mapping[str, Any]) -> str:
    parts = [raw.get("summary") or "", raw.get("description_text") or ""]
    for c in raw.get("comments") or []:
        parts.append(c.get("body_text") or "")
    return "\n".join(parts)


def substance_metrics(raw: Mapping[str, Any]) -> dict[str, int | str | bool]:
    desc = (raw.get("description_text") or "").strip()
    comments = raw.get("comments") or []
    comm_text = "\n".join((c.get("body_text") or "").strip() for c in comments)
    comm_non_verify = sum(
        1
        for c in comments
        if (c.get("body_text") or "").strip()
        and not _VERIFIED_ONLY.match((c.get("body_text") or "").strip())
    )
    desc_len = len(desc)
    comm_len = len(comm_text)
    total = desc_len + comm_len
    blob = text_blob(raw)

    if total < 50:
        tier = "empty"
    elif total < 200:
        tier = "thin"
    elif total < 800:
        tier = "medium"
    else:
        tier = "rich"

    return {
        "description_chars": desc_len,
        "comment_chars": comm_len,
        "substance_chars": total,
        "substance_tier": tier,
        "rule_like": bool(_RULE_LIKE.search(blob)),
        "has_meaningful_comment": comm_non_verify > 0,
    }


def should_distill_queue(
    raw: Mapping[str, Any],
    *,
    material_kind: str,
    issuetype: str,
) -> bool:
    """
  True = 建议进入 D-extract（Jira业务规则摘录）队列，非仅索引。

  比 business_extract 更严：须有可抽文本或缺陷结论。
    """
    if material_kind == "collaboration_noise":
        return False
    m = substance_metrics(raw)
    itype = (issuetype or "").lower()
    if "bug" in itype or "defect" in itype:
        return m["substance_chars"] >= 80 or m["has_meaningful_comment"]
    if material_kind != "normative_business":
        return False
    if m["substance_tier"] in ("medium", "rich"):
        return True
    if m["substance_tier"] == "thin" and m["rule_like"]:
        return True
    return False
