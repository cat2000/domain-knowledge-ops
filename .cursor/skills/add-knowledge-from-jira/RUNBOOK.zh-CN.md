# add-knowledge-from-jira · 执行剧本（Agent 必读）

> English SSOT: [`RUNBOOK.md`](./RUNBOOK.md).
>
> **读者**：Cursor Agent（**Ingest** 完成后 **必须** 读本文件）。  
> **入口**：[`SKILL.md`](./SKILL.md) · **Ingest**：[`INGEST-CLI.md`](./INGEST-CLI.md) · **Classify**：[`CLASSIFY-CLI.md`](./CLASSIFY-CLI.md) · **Compose**：[`generate-knowledge-from-wiki/RUNBOOK.md`](../generate-knowledge-from-wiki/RUNBOOK.md)  
> **契约**：[`../../contracts/domain-knowledge-pipeline-contract.md`](../../contracts/domain-knowledge-pipeline-contract.md) §1、§4 · **质量栏**：`domain-knowledge/distill-quality-bar.md`

---

## 管线总览（Jira 备料 + 统一 Compose）

Jira 负责提供业务细则证据：AC、评论、状态流转、阈值、last-wins 决策。Confluence 与 Jira 的差异只在 **Ingest/Classify**；一旦进入成稿，二者必须进入同一 **S3→S6 Compose** 主线。Jira 不再作为 S6 后补丁或“实现口径附录”。

| 阶段 | 归属 | 含义 | 执行者 | 停闸 |
|------|------|------|--------|------|
| **Ingest** | Jira | 拉票 → `raw/`（+ 可选 `materialized/` 可读副本） | 脚本 | — |
| **Classify** | Jira | 票级分诊 → `attribution/`、主题索引 | 脚本 + Cursor B1 | — |
| **Recognize** | **共用** | 命题认域 + closure + 人 **`确认`** | Cursor | **完整备料末：停** |
| **Compose** | **共用** | S3→S4→S5→S6；S3 同时读 Confluence 与 Jira 业务证据 | Cursor | 仅 **`确认`** 行 |

### 备料 vs 成稿（停闸）

| 称谓 | 阶段 | 执行者 | 停在哪 |
|------|------|--------|--------|
| **脚本备料** | Ingest + Classify | `run_jira_knowledge.py`（history 拉到当前 sprint；或 `--sprint-id` 单 Sprint） | `domain_check jira --full-raw` → **停**（Agent 接 Recognize） |
| **完整备料** | + Recognize | Cursor（Wiki RUNBOOK · [S2 认域](../generate-knowledge-from-wiki/RUNBOOK.md#s2--认域--全库打标备料末步--命题级)） | 确认页 + closure → **停**等人标 **`确认`** |
| **成稿** | 统一 Compose | Cursor + Wiki RUNBOOK | 仅 **`确认`** 行；`_aggregate/` 应出现 `source_system: jira` |

**落盘根**：`domain-knowledge/curated/by-root/<R>/`（与 Wiki 相同 `root_id`，见 `team-roots.json`）。

### 与 Wiki 三阶段对照

| Wiki | Jira |
|------|------|
| Ingest（sync + facet 粗分） | **Ingest**（fetch；**无** facet 目录） |
| Recognize | **Classify attribution** → **Recognize**（共用确认门） |
| Compose（S3→S6） | **Compose**（共用；Jira 业务票在 S3 输入层并入） |

### 用户话术 → CLI

| 用户 `mode=` | Agent 应跑 |
|--------------|------------|
| `history` + `team=<t>` | `run_jira_knowledge.py --team <t>`；team 映射到 board id，从最早 Sprint 拉到当前 Sprint（含当前） |
| `history` + `board-id=<id>` | 按 `team-roots.json` 映射到 team，再执行同上 |
| `sprint` + `sprint-id` | `run_jira_knowledge.py --team <resolved-team> --sprint-id <id>`；只拉该 Sprint |
| `compose` / `继续` | Wiki RUNBOOK Compose；S3 自动纳入 Jira 业务票 |
| `distill` / `reconcile` / `full` | 旧路径已删除；拒绝执行，改走备料 → Recognize → Compose |

### 操作编号（脚本 / 门禁）

| 阶段 | 常用脚本 / 文档 |
|------|-----------------|
| Ingest | `run_jira_ingest.py` · [`INGEST-CLI.md`](./INGEST-CLI.md) |
| Classify | `run_jira_knowledge.py` · [`CLASSIFY-CLI.md`](./CLASSIFY-CLI.md) |
| Recognize | [Wiki RUNBOOK · S2 认域](../generate-knowledge-from-wiki/RUNBOOK.md#s2--认域--全库打标备料末步--命题级) |
| Compose | [Wiki RUNBOOK · Compose](../generate-knowledge-from-wiki/RUNBOOK.md#compose成稿--s3--s6仅-确认-主题)（S3–S6） |

---

## Ingest · 拉票（脚本）

入口：`python3 scripts/run_jira_ingest.py`（默认 **仅 fetch** → `raw/`；`--materialize` 或 `materialize.py` → `jira/materialized/`）。

| 策略 | 命令 | 含义 |
|------|------|------|
| **指定 Sprint** | `--mode sprint --sprint-id <id>` | 该 Sprint **全部**票 + comments |
| **Board 历史拉满** | `--mode history --until-complete` | 从最早 Sprint 逐个拉到当前 Sprint（含当前） |

1. 代跑 Ingest；读 `jira/JIRA_PIPELINE_HANDOFF.json`。
2. 验收：`jira/raw/*.json` 数量合理（`materialized/` 与 `raw/` 1:1 若已物化）。
3. 进入 **Classify**（或 `run_jira_knowledge.py` 一并跑 Ingest + Classify + **Classify 门禁**）。

参数与排障见 [`INGEST-CLI.md`](./INGEST-CLI.md)。

**SSOT**：脚本与归因读 **`raw/`**；`materialized/` 供 Cursor closure/人工阅读（ faithful md，**非**权威）。

---

## Classify · 分诊（脚本备料 · Jira 专有）

**CLI 参数 / 排障**：[`CLASSIFY-CLI.md`](./CLASSIFY-CLI.md)
**运行规则**：[`jira_classify.mdc`](../../rules/jira_classify.mdc)

**目的**：扁平工单 → 命题 slug、摘录队列、主题索引。**不是**命题级认域（那是 **Recognize**）。

| 动作 | 产出 | 执行者 |
|------|------|--------|
| `python3 scripts/jira/steps/attribute.py --team <t>` | `attribution/<KEY>.yaml`、`_ticket_attribution.json` | 脚本 |
| `python3 scripts/jira/steps/read_business.py --team <t>` | `by-theme/<t>/遗漏扫描.md`（**索引**；主题来自 **attribution**，见 [`CLASSIFY-CLI.md`](./CLASSIFY-CLI.md)） | 脚本 |
| 人标 **`确认`** 后可选 | `read_business.py --confirmed-only` | 脚本 |
| Cursor 复核低置信 attribution | 修正 `jira/attribution/` 下 YAML | Cursor |

**禁止**：用票级 attribution 覆盖率代替 **Recognize** 完成；将 sink slug（`gateway` / `requirements` 或团队配置的 sinks）当作已 **确认** 的业务命题。

**Classify 门禁**：`python3 scripts/domain_check.py jira --team <t> --full-raw`（脚本备料末）

---

## Recognize · 认域（完整备料末步 · 与 Wiki 共用）

执行 [Wiki RUNBOOK · S2 认域](../generate-knowledge-from-wiki/RUNBOOK.md#s2--认域--全库打标备料末步--命题级)：**同一** `DOMAIN_MODULE_CHECKLIST.md`、`_materialization_closure.json`、人标 **`确认`**。

Jira 在 S2 不重新按文件全文扫一遍；它把 Classify 产出的 `primary`、`themes[]`、`distill_tier`、`proposition_id` 映射到统一确认门。若映射不合理，Agent 应修正 `attribution/*.yaml`，再重跑 S2。

| 动作 | 产出 |
|------|------|
| `strategy.md` §2 × 领域块 | `DOMAIN_MODULE_CHECKLIST.md` |
| Confluence：扫描 S1 manifest/materialized；Jira：读取 `attribution/*.yaml` | `_materialization_closure.json`（**索引**，禁止多目录贴全文） |
| 非业务页 | Pass 占位 |

**完整备料完成汇报**：Classify 索引齐；确认页 + closure 齐；**尚无** 摘录 / 定稿。**暂停** → 人标 **`确认`**。

**建议门禁**：`python3 scripts/distill/coverage.py --root-id <R>`

---

## 人工闸门 · 领域模块确认

与 Wiki **完全相同**（[`domain-module-checklist.mdc`](../../rules/domain-module-checklist.mdc)）：

| 动作 | 说明 |
|------|------|
| 人编辑确认页 | 认可行 **「状态」** → **`确认`** |
| **`继续`** | 对 **`确认` 行** 执行统一 Compose（S3→S6） |
| 尚无 **`确认`** | **不** 跑 Compose |

---

## 成稿（仅 **`确认`** 主题）

**顺序**：执行 [`generate-knowledge-from-wiki/RUNBOOK.md`](../generate-knowledge-from-wiki/RUNBOOK.md) 的 **Compose**（S3→S6）。S3 proposition extraction 只读取 S2 closure 中已授权给确认 slug 的 source；被 S2 closure 指向该 slug 的 `jira/materialized/<KEY>.md` 与 Confluence materialized pages 会进入同一命题候选层。

### Compose · 统一定稿主体（Cursor · mandatory）

**必须**执行 [`generate-knowledge-from-wiki/RUNBOOK.md`](../generate-knowledge-from-wiki/RUNBOOK.md) **[§Compose](../generate-knowledge-from-wiki/RUNBOOK.md#compose成稿--s3--s6仅-确认-主题)**（S3 归集 → S4 领域模型 → S5 工作稿 → S6 中文定稿）。

S3 准入：

- Confluence：按 `_materialization_closure.json` 与已确认 slug 读取。
- Jira：按 `attribution/<KEY>.yaml` 的 `primary/themes[]` 命中已确认 slug，并且 `distill_tier` 为 `proposition_core` / `platform_variant`。
- 明确排除 `engineering_slice`、`cross_theme_ref`、`index_only`，除非 Agent 基于业务后果重新归因并修正 attribution。

**门禁**：S6 后 `python3 scripts/domain_check.py distill --root-id <R>`。

---

## 脚本编排（`run_jira_knowledge.py`）

| 命令 | 编排 |
|------|------|
| （无 flag） | **Ingest**（从最早 Sprint 到当前 Sprint，含当前）+ **Classify** + Classify 门禁 → **停闸**（Agent 接 Recognize） |
| `--sprint-id <id>` | **Ingest**（仅指定 Sprint）+ **Classify** + Classify 门禁 → **停闸** |

仅 Ingest 细参：`python3 scripts/run_jira_ingest.py …`

---

## 用户话术

| 意图 | 说法 |
|------|------|
| 仅 Ingest · 指定 Sprint | `@add-knowledge-from-jira team=demo mode=sprint sprint-id=1726` |
| Ingest · Board 历史拉满 | `@add-knowledge-from-jira team=demo mode=history` 或 `board-id=<id> mode=history` |
| 脚本备料 | `mode=history` 或 `run_jira_knowledge.py`（无 flag） |
| Compose（统一定稿） | **`继续`** + Wiki RUNBOOK |
| 已删除旧路径 | `mode=distill/reconcile/full`；拒绝执行并改走统一 Compose |

---

## 汇报模板

- **Ingest**：Sprint id/名、本批 keys、`jira/raw/` 路径
- **Classify + Recognize / 完整备料**：attribution 覆盖；确认页 **已确认 / 待确认** 行数；closure
- **Compose**：各 **确认** 主题：`_aggregate/*-命题清单.md` 是否出现 Jira 来源；工作稿 / 定稿 **有/无**；Jira 业务细则是否被并入正文规则链
- **禁止**：仅有 attribution 或索引却报「Jira 管线完成」

---

## 附录 · 步骤速查

### 阶段 ↔ 产物 ↔ 门禁

| 阶段 | Agent 必读 | 主要写入 | 门禁 |
|------|------------|----------|------|
| Ingest | `INGEST-CLI.md` | `jira/raw/`、`jira/materialized/` | 脚本退出码 |
| Classify | `CLASSIFY-CLI.md` | `attribution/`、`遗漏扫描.md` | `domain_check jira --full-raw` |
| Recognize | Wiki RUNBOOK · S2 | 确认页、closure | `coverage.py`（建议） |
| Compose | Wiki RUNBOOK · Compose | `_aggregate/`、工作稿、定稿 | `domain_check distill` |

### 产物三层（不变量）

| 层级 | 角色 |
|------|------|
| 索引 | 地图、KEY 清单 |
| 证据 | `raw/` 是正本；`attribution/` 是 S2 准入依据；`materialized/` 是 S3 可读副本 |
| 并入 | 统一 Compose 正文中的业务规则链（非文末 Jira 附录） |

历史根因见 [`pipeline-design.md`](../../../domain-knowledge/jira/pipeline-design.md) §一，**不作为**门禁条文。

## Next

`@requirement-risk` → `@ticket-splitter` → `@ticket-test-design`（证据：`_deliver/…定稿.md`）。
