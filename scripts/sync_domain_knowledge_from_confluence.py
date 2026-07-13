#!/usr/bin/env python3
"""
Wiki **S1**：从 Confluence 页/子树 **同步** 到 ``domain-knowledge``（``extracted/`` + ``materialized/``）。

枚举 → 逐页抽取 → 完整性门禁 → source-coverage → facet 物化（manifest 清理旧输出，可选跳过）。
**不**写 ``curated/``、**不**调 LLM；
S2–S6 由 Cursor 按 ``generate-knowledge-from-wiki/RUNBOOK.md`` 完成。

**任意根页面 ID**（URL 或数字）均写入同一布局，按 Page ID 去重（同 ID 覆盖更新）：

  domain-knowledge/extracted/by-root/<ROOT_PAGE_ID>/
    descendants-full.json
    source-coverage.md
    pages/<PAGE_ID>.md

  domain-knowledge/materialized/by-root/<ROOT_PAGE_ID>/
    facet-*/…              # 除非 --skip-materialize

Usage:
  python3 scripts/sync_domain_knowledge_from_confluence.py --root 48696506
  python3 scripts/sync_domain_knowledge_from_confluence.py --url 'https://.../pages/12345/Some+Page'
  python3 scripts/sync_domain_knowledge_from_confluence.py --url 'https://.../wiki/spaces/CMA/overview'
  python3 scripts/sync_domain_knowledge_from_confluence.py --url '...' --allow-partial

Space ``…/overview`` URL 需 **ATLASSIAN_EMAIL** + **ATLASSIAN_API_TOKEN** 解析 Space 首页。

默认 **枚举根 = 粘贴页**（或 ``--root``）。可选祖先升格见 ``CONFLUENCE_CANONICAL_ROOT_IDS``。
默认 **复用已有团队 by-root**（子树刷新合并页清单）；``--no-reuse-existing-by-root`` 关闭。

Implementation: ``scripts/wiki/sync/pipeline.py``.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = next(p for p in Path(__file__).resolve().parents if (p / "_install.py").is_file())
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
import _install

_install.bootstrap(__file__)

from wiki.sync.pipeline import main  # noqa: E402

if __name__ == "__main__":
    main()
