# add-knowledge-from-jira · Classify CLI（参数 / 排障）

> English SSOT: [`CLASSIFY-CLI.md`](./CLASSIFY-CLI.md).
>
> **阶段**：**Classify** · **剧本**：[`RUNBOOK.md`](./RUNBOOK.md) · **入口**：[`SKILL.md`](./SKILL.md)  
> **前置**：[`INGEST-CLI.md`](./INGEST-CLI.md)（`jira/raw/` 须已存在）

**Classify ≠ Recognize**：本阶段是票级分诊（`attribution/`、主题索引）；命题级认域 + 人 **确认** 在 Wiki RUNBOOK · S2。

## 编排 vs 单步

| 方式 | 命令 | 何时用 |
|------|------|--------|
| **推荐备料** | `python3 scripts/run_jira_knowledge.py --team <t>` | 历史至当前 Sprint + Classify + `--full-raw` → **停** |
| **仅 Classify** | raw 已有时再跑 attribute + read_business + check | Ingest 已完成 |
| **跳过 Classify** | `run_jira_knowledge.py --skip-attribute` | 维护者调试 only |

Classify 段：`attribute.py` → `read_business.py` → `domain_check.py jira --team <t> --full-raw`

## attribute

```bash
python3 scripts/jira/steps/attribute.py --team demo
python3 scripts/jira/steps/attribute.py --team demo --keys PROJ-1,PROJ-2
python3 scripts/jira/steps/attribute.py --team demo --no-preserve-cursor-reviewed
```

| 参数 | 含义 |
|------|------|
| `--team` | `team-roots.json` 中的 team key（必填） |
| `--keys` | 逗号 KEY；省略 = 全部 `raw/*.json` |
| `--no-preserve-cursor-reviewed` | 覆盖已有 `cursor_review` / 高置信 YAML（慎用） |

字段语义：[`first-principles-attribution.md`](../../../domain-knowledge/jira/first-principles-attribution.md) · 团队规则 `domain-knowledge/jira/teams/<team>.json`（**词表在团队配置，不在 pack 默认特例**）。

低置信票：在 Cursor 中复核并修正 YAML。

## read_business / 门禁

```bash
python3 scripts/jira/steps/read_business.py --team demo
python3 scripts/jira/steps/read_business.py --team demo --theme <slug>
python3 scripts/jira/steps/read_business.py --team demo --confirmed-only
python3 scripts/domain_check.py jira --team demo --full-raw
```

主题列表默认来自 attribution ∩ checklist allowed；`--confirmed-only` 仅 **确认** 行。无 pack 内硬编码业务主题 fallback。

票有 attribution ≠ 管线完成；随后进入共享 Recognize。

## 命令速查

```bash
python3 scripts/run_jira_knowledge.py --team demo
python3 scripts/jira/steps/attribute.py --team demo
python3 scripts/jira/steps/read_business.py --team demo
python3 scripts/domain_check.py jira --team demo --full-raw
```

## 故障排查

| 现象 | 处理 |
|------|------|
| `missing attribution/…` | 先跑 `attribute.py` |
| `skip unknown theme` | slug 不在 checklist / `teams/<team>.json`；补 setup 或团队配置 |
| 多数 `business_extract: false` | 正常；索引队列 ≠ S3 业务证据准入 |
