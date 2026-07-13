> English SSOT: [`jira_classify.mdc`](./jira_classify.mdc).

# Jira Classify 护栏

适用：Jira Classify（`attribute` / `read_business` / `run_jira_knowledge.py` 的 Classify 段）。

## 执行顺序

1. `attribute.py` 先跑，生成 `attribution/<KEY>.yaml` 与 `_ticket_attribution.json`
2. `read_business.py` 后跑，生成 `by-theme/<slug>/gap-scan.md`（中文 locale 常见为 `遗漏扫描.md`）
3. `domain_check.py jira --full-raw` 作为 Classify 门禁

## 口径约束

- 主题索引 / `遗漏扫描` 是 **索引层**，不是 Extract 完成信号
- `gateway` / `requirements` 是分诊兜底桶，不得升格为 checklist 已确认命题
- 默认 `read_business` 按 attribution 主题扫描；人标 `确认` 后可 `--confirmed-only` 刷新
- 脚本主数据源是 `jira/raw/`；`materialized/` 仅用于阅读与 closure 索引

## Cursor 复核（B1）

- 团队配置了低置信 / `cursor_review` 票时，必须先复核再宣称 Classify 完成
- 团队专项说明见 `domain-knowledge/jira/teams/<team>.json`（及可选 `*-attribution.md`）

## 禁止

- 仅凭 attribution 覆盖率宣称管线完成
- 未经 `domain_check jira --full-raw` 直接进入后续阶段
