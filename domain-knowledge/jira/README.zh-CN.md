> English SSOT: [`README.md`](./README.md).

# Jira → 领域知识库（业务细则证据）

Jira 是业务细则的一等来源：AC、评论、状态流转、阈值和 last-wins 决策应与 Confluence 一起进入同一 `curated/by-root/<根>/` Compose 主线。

**Agent 唯一剧本**：[`.cursor/skills/add-knowledge-from-jira/RUNBOOK.md`](../../.cursor/skills/add-knowledge-from-jira/RUNBOOK.md)  
**用户入口**：[`.cursor/skills/add-knowledge-from-jira/SKILL.md`](../../.cursor/skills/add-knowledge-from-jira/SKILL.md)  
**Ingest 参数**：[`.cursor/skills/add-knowledge-from-jira/INGEST-CLI.md`](../../.cursor/skills/add-knowledge-from-jira/INGEST-CLI.md)  
**Classify 参数**：[`.cursor/skills/add-knowledge-from-jira/CLASSIFY-CLI.md`](../../.cursor/skills/add-knowledge-from-jira/CLASSIFY-CLI.md)

**约束**：禁止外挂 LLM API。Ingest、Classify 为确定性脚本备料；Recognize、Compose 为 Cursor 语义判断。旧 Extract/Integrate 已删除，不再保留审计入口。

**第一性归属**：[first-principles-attribution.zh-CN.md](first-principles-attribution.zh-CN.md)（英：[first-principles-attribution.md](first-principles-attribution.md)）  
**三层产物与历史根因**：[pipeline-design.zh-CN.md](pipeline-design.zh-CN.md)（英：[pipeline-design.md](pipeline-design.md)）  
**团队归属**：[`teams/demo.json`](teams/demo.json)、`teams/<team>.json`（见 [`team-roots.json`](team-roots.json)）

## 管线（Jira 备料 + 统一 Compose）

| 阶段 | 执行者 | 产物 |
|------|--------|------|
| **Ingest** | `run_jira_ingest.py` | `jira/raw/`、`jira/materialized/` |
| **Classify** | `attribute.py` + `read_business.py` + Cursor | `attribution/`、主题索引 |
| **Recognize** | Cursor（[Wiki RUNBOOK](../../.cursor/skills/generate-knowledge-from-wiki/RUNBOOK.md)） | Jira attribution 映射到共用 `DOMAIN_MODULE_CHECKLIST.md`、closure |
| **Compose** | Cursor（统一 **S3→S7**） | `_aggregate/`、工作稿、源语定稿、本地语言定稿；S3 读入 Jira business evidence |

逐步说明见 **[`add-knowledge-from-jira/RUNBOOK.md`](../../.cursor/skills/add-knowledge-from-jira/RUNBOOK.md)**。

## 团队与配置

团队表以 **[`team-roots.json`](team-roots.json)**（**v3**：`libraries` + `teams` 挂载）与 **`scripts/teams/registry.py`** 为准。默认示例：`demo` 库 + 团队（`board_id=1`）。模板：[`team-roots.example.json`](team-roots.example.json)。

**Ingest（拉票）**：

| 命令 | 产物 |
|------|------|
| `run_jira_ingest.py --mode sprint --sprint-id <id>` | `jira/raw/<KEY>.json` |
| `run_jira_ingest.py --mode history --until-complete` | 从最早 Sprint 逐个拉到当前 Sprint（含当前）+ `sync-state.json` |
| 可选 materialize | `jira/materialized/<KEY>.md` |

Sprint 队列：`jira/lib/jira_sprints.py` → `sprints-closed.json`。

## 目录布局

```text
domain-knowledge/curated/by-root/<root_id>/jira/
  sync-state.json
  batch-manifest.json
  JIRA_PIPELINE_HANDOFF.json
  raw/<KEY>.json
  materialized/<KEY>.md
  attribution/<KEY>.yaml
  _ticket_attribution.json
  by-theme/<主题>/
    全量KEY索引.md、遗漏扫描.md     # 索引（Classify）
```

## 脚本编排（`run_jira_knowledge.py`）

| 命令 | 含义 |
|------|------|
| （无 flag） | **备料**：board 历史拉满（含当前 Sprint）+ Classify + 门禁 → **停闸** |
| `--sprint-id <id>` | **备料**：只拉指定 Sprint + Classify + 门禁 → **停闸** |

## 调用示例

```text
@add-knowledge-from-jira team=demo mode=history
@add-knowledge-from-jira board-id=1 mode=history
@add-knowledge-from-jira team=demo mode=sprint sprint-id=<id>
```

## 推荐命令序

```bash
# 备料
python3 scripts/run_jira_knowledge.py --team demo
python3 scripts/run_jira_knowledge.py --team demo --sprint-id <id>

# 成稿：确认页已标 确认 后，执行 generate-knowledge-from-wiki RUNBOOK Compose（S3→S7）

# 门禁
python3 scripts/domain_check.py jira --team demo --full-raw
python3 scripts/domain_check.py distill --root-id 100001
```

## 质量

- 与 Confluence 定稿并列溯源：**Jira KEY + Confluence 链**。
- 跨票冲突：**`effective_at` 晚者优先**；仍冲突标 **待核**。
- **S3 准入**：`distill_tier=proposition_core/platform_variant`。
- **Recognize 准入**：Jira 不按 materialized 文件重新认域；以 `attribution/*.yaml` 的 `primary/themes[]/distill_tier/proposition_id` 进入同一确认门。
- **完成定义**：已确认主题的 `_aggregate/`、工作稿、定稿都能看到 Jira 业务细则被语义合并，非票级覆盖率。

## 层级关联（`parent` 字段）

除 **issuelinks** 外，团队大量使用 Jira **`fields.parent`**：

| 机制 | 用途 |
|------|------|
| **`parent` / `parent_key`** | 子票 → 直接父级 |
| **`parent_chain`** | 可选：`--resolve-parent-chain` |
| **`_parent_index.json`** | 本批 raw 汇总 |

**Classify**：有 `parent` 时优先读父级摘要；`themes` 可继承父级，子票评论可覆盖。
