# add-knowledge-from-jira · Ingest CLI（参数 / 排障）

> English SSOT: [`INGEST-CLI.md`](./INGEST-CLI.md).
>
> **阶段**：**Ingest**（Jira 四阶段之 ①）  
> **执行剧本**：[`RUNBOOK.md`](./RUNBOOK.md) · **用户入口**：[`SKILL.md`](./SKILL.md) · **备料编排**：`scripts/run_jira_knowledge.py`  
> **入口脚本**：`scripts/run_jira_ingest.py`

## 两种拉取策略（仅此两种）

| 策略 | CLI | 含义 |
|------|-----|------|
| **指定 Sprint** | `--mode sprint --sprint-id <id>` | 拉该 Sprint **全部** issue（含 comments）；默认 **不** 推进 `sprint_cursor` |
| **Board 历史拉满** | `--mode history --until-complete` | 按 board 的 `sprints-closed.json` 从最早 Sprint 逐个拉到当前 Sprint（含当前），直到 `sprint_cursor.completed=true` |

**SSOT**：Jira 归因读 `raw/` + `attribution/`；S3 证据准入读 S2 closure；`materialized/` 供 S3 / Cursor / 人工阅读（faithful md，**非**权威）。

团队 / board / `root_id`：**[`team-roots.json`](../../../domain-knowledge/jira/team-roots.json)** · **`scripts/teams/registry.py`**。`team=cma` 与 `board_id=150` 等价，脚本解析后都会落到同一个 Jira board。

## 编排脚本内部顺序

入口：`scripts/run_jira_ingest.py`（默认 **仅 fetch**）。

1. `jira/steps/fetch.py` → `jira/raw/<KEY>.json`（description + 全部 comments）
2. （可选）`jira/steps/materialize.py` → `jira/materialized/<KEY>.md` — **`--materialize`** 或单步调用

`run_jira_knowledge.py` 备料：默认 **history until-complete fetch** → **单独一步 materialize**（Recognize closure 路径）→ Classify；带 `--sprint-id` 时只拉指定 Sprint。

单步调试可跳过编排：

```bash
python3 scripts/jira/steps/fetch.py --team cma --mode sprint --sprint-id 1726
python3 scripts/jira/steps/materialize.py --team cma
```

**`attribution/`、`curated/_deliver/`**：Ingest **不写**；**Classify** 见 [`CLASSIFY-CLI.md`](./CLASSIFY-CLI.md)。

## Sprint 队列

- 刷新队列：`python3 scripts/jira/lib/jira_sprints.py --team <t>`
- 缓存：`curated/by-root/<R>/jira/sprints-closed.json`
- 游标：`sync-state.json` → `sprint_cursor`

`--refresh-sprints`：fetch 前重建队列。`--reset`：清空游标后重跑。

## 命令速查

```bash
# 指定 Sprint（fetch only）
python3 scripts/run_jira_ingest.py --team cma --mode sprint --sprint-id 1726

# Board 历史拉满（fetch only）
python3 scripts/run_jira_ingest.py --team cma --mode history --until-complete

# fetch + materialize
python3 scripts/run_jira_ingest.py --team cma --mode history --until-complete --materialize

# board_id 与 team 等价
python3 scripts/run_jira_ingest.py --team 150 --mode history --until-complete --materialize

# 队列已完成仍强制再拉一轮（history）
python3 scripts/run_jira_ingest.py --team cma --mode history --fetch

# 仅物化（raw 已有）
python3 scripts/jira/steps/materialize.py --team cma
```

## 故障排查

| 现象 | 处理 |
|------|------|
| `HTTP 401/403` | `.env` 中 `ATLASSIAN_EMAIL`、`ATLASSIAN_API_TOKEN`；Jira 项目权限 |
| `Sprint id … not in queue` | `--refresh-sprints` 或检查 board / `team-roots.json` |
| `no issues returned` | 空 Sprint；检查 JQL / Sprint 状态 |
| 很慢 | 票数 ×（issue + comments REST）；预期 |

## 产物路径

```text
domain-knowledge/curated/by-root/<root_id>/jira/
  raw/<KEY>.json
  materialized/<KEY>.md
  sync-state.json
  batch-manifest.json
  JIRA_PIPELINE_HANDOFF.json
```
