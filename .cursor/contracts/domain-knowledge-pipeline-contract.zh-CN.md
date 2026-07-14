> English SSOT: [`domain-knowledge-pipeline-contract.md`](./domain-knowledge-pipeline-contract.md).

# 领域知识库 · 跨流水线契约

> **读者**：维护者、Cursor Agent。  
> **范围**：Confluence 同步、蒸馏、`curated`、Jira 补充、手动上传 — **不变量**与 **产物分层**。  
> **专有条目**：各 Skill 只写本流水线独有步骤。

| 文档 | 用途 |
|------|------|
| [`domain-knowledge/strategy.md`](../../domain-knowledge/strategy.md) | Methodology template + fill-in industry (§2)；人裁 SSOT · [`strategy.zh-CN.md`](../../domain-knowledge/strategy.zh-CN.md) |
| [`domain-knowledge/s2-domain-profiles.json`](../../domain-knowledge/s2-domain-profiles.json) | 机器主题/facet（由 strategy 派生；默认空壳） |
| [`domain-knowledge/distill-quality-bar.md`](../../domain-knowledge/distill-quality-bar.md) | 三层基线 · zh: [`distill-quality-bar.zh-CN.md`](../../domain-knowledge/distill-quality-bar.zh-CN.md) |
| [`domain-knowledge/distill-document-skeleton.md`](../../domain-knowledge/distill-document-skeleton.md) | 工作稿骨架 · zh: [`distill-document-skeleton.zh-CN.md`](../../domain-knowledge/distill-document-skeleton.zh-CN.md) |
| [`domain-knowledge/language/glossary.md`](../../domain-knowledge/language/glossary.md) | 统一语言 |
| [`domain-knowledge/language/deliverable-locale-tokens.json`](../../domain-knowledge/language/deliverable-locale-tokens.json) | 本地语言标签/文件名（`deliverable_locale`） |
| [`domain-knowledge/jira/team-roots.json`](../../domain-knowledge/jira/team-roots.json) | v3：`libraries`（space/`root_id`/deliver）+ `teams`（board + 挂载） |

---

## 1. 产物分层（仓库路径）

| 层 | 路径 | 谁写 | 对外承诺？ |
|----|------|------|------------|
| 抽取 | `extracted/by-root/<落盘根>/` | 脚本 | 否（中间物） |
| 物化素材 | `materialized/by-root/<落盘根>/` | 脚本 | 否（忠实同步，多英文） |
| 按块聚合 | `curated/.../_aggregate/<slug>/` | Cursor（S3） | 否 |
| 蒸馏工作稿 | `.../_deliver/<slug>/*-工作稿.md` / `*-work-draft.md` | Cursor（S4/S5） | 否 |
| 原语言定稿 | `.../_deliver/<slug>/*-source-brief.md` | Cursor（**S6**） | 否（中间裁决稿） |
| **目标语言定稿** | `.../_deliver/<slug>/*-领域知识定稿.md` 或 `*-domain-brief.md` | Cursor（**S7**） | **是** |
| Jira 旁路 | `.../jira/by-theme/<主题>/` | 脚本 + Cursor | 索引/归因；并入定稿见 Compose |
| 术语 | `domain-knowledge/language/glossary.md` | 脚本（S7 后）+ 人 | 全库 |

**正本**：Confluence 源页。改业务事实 → 改 Confluence → 再跑同步，**勿**长期手改 `materialized/` 当作权威。

---

## 2. 枚举根 vs 落盘根（Confluence 同步）

| 概念 | 含义 |
|------|------|
| **枚举根** | 粘贴链接解析的 Page ID（可选祖先升格）。决定 **本轮拉哪棵子树**。 |
| **落盘根** | `by-root/<ID>/` 中的 `<ID>`。`extracted/`、`materialized/`、`curated/` **共用**。 |

- **Space overview**：枚举根 ≈ 落盘根 ≈ Space 首页 ID（整库刷新）。
- **子页链接 + 默认复用**：枚举根 = 子页；落盘根常 = 已有团队整库 ID。勿新建并列 `by-root/<子页ID>/`。
- 关闭复用：`--no-reuse-existing-by-root` 或 `CONFLUENCE_REUSE_EXISTING_BY_ROOT=0` → 落盘根 = 枚举根。

**`PIPELINE_HANDOFF.json`**（`extracted/by-root/<落盘根>/`）：`root_page_id` = 落盘根；若有 `enumeration_root_page_id` 则与落盘根不同。蒸馏与门禁脚本 **一律用落盘根**。

---

## 3. Wiki 流水线（`@generate-knowledge-from-wiki`）

**主叙事三阶段**：**Ingest**（S1）→ **Recognize**（S2）→ **Compose**（S3→S7）。**S1–S7** 仍为操作编号。**备料** = Ingest + Recognize；**成稿** = Compose。

| 阶段 | 步 | 产物 | 执行者 |
|------|-----|------|--------|
| Ingest | S1 | `extracted/`、`materialized/` | `sync_domain_knowledge_from_confluence.py` |
| Recognize | S2 | 确认页、closure | Cursor |
| Compose | S3–S7 | `_aggregate/`、工作稿、source brief、locale brief | Cursor |

**唯一执行剧本**：[`generate-knowledge-from-wiki/RUNBOOK.md`](../skills/generate-knowledge-from-wiki/RUNBOOK.md)

- 用户入口：[`generate-knowledge-from-wiki/SKILL.md`](../skills/generate-knowledge-from-wiki/SKILL.md)
- 仅 Recognize / Compose、不跑 Ingest：[`distill-domain-knowledge/SKILL.md`](../skills/distill-domain-knowledge/SKILL.md) → 仍读 RUNBOOK

**不变量（摘要）**：禁止仓库 HTTP LLM 整理稿；抽取默认不全文翻译（目标语言仅 **S7**）；同轮 `@generate-knowledge-from-wiki` **必须** Ingest → Recognize → Compose（S1→S7），不得只停在 `materialized/`。

---

## 4. Jira 流水线（`@add-knowledge-from-jira`）

**唯一执行剧本**：[`add-knowledge-from-jira/RUNBOOK.md`](../skills/add-knowledge-from-jira/RUNBOOK.md) · **Recognize + Compose** 共用 [`generate-knowledge-from-wiki/RUNBOOK.md`](../skills/generate-knowledge-from-wiki/RUNBOOK.md)

**主叙事**：**Ingest → Classify → Recognize**（共用）→ **Compose**（Wiki S3→S7）。旧 Extract / Integrate 已删除。

| 阶段 | 执行者 | 产物 |
|------|--------|------|
| Ingest | `run_jira_ingest.py` | `jira/raw/`、`jira/materialized/` |
| Classify | `attribute.py` + `read_business.py` + Cursor | `attribution/`、主题索引 |
| Recognize | Cursor（Wiki RUNBOOK） | 共用确认页、closure |
| Compose | Cursor（Wiki RUNBOOK S3–S7） | `_aggregate/`、工作稿、source brief、locale brief |

主编排：`scripts/run_jira_knowledge.py`（仅 **脚本备料** Ingest+Classify）。

- **脚本备料** = Ingest + Classify + `domain_check jira --full-raw` → 停；**完整备料** 另加 Cursor Recognize（Wiki RUNBOOK · S2）
- **完成定义（机器）**：`domain_check jira --full-raw` 验证备料；`domain_check distill` 验证 Compose 后定稿质量
- **不变量**：票级覆盖率 ≠ 完成；已确认主题须在 `_aggregate/`、工作稿、定稿中吸收 Jira business evidence
- **命题 `primary`** = 已确认 **slug**，不是 `requirements`/`gateway` 兜底桶

团队配置：`team-roots.json` · 路径 SSOT：`scripts/teams/registry.py`。

---

## 5. Teams / `root_id`（配置驱动 · 任意 N 个）

SSOT：`domain-knowledge/jira/team-roots.json`（模板：`team-roots.example.json`）。

- `teams` 对象有几个 key，就有几个团队；key 自定（`demo`、`orders`、`mobile`…）。
- 可选 `defaults.default_team`：CLI 省略 `--team` 时的默认。
- 本仓库默认只带一个 `demo` 团队与 **空** `checklist_themes`；填实 `strategy.md` §2 并派生 profiles 后再认域。

```bash
python3 -c "from teams.registry import load_team_roots; print(list(load_team_roots()))"
```

---

## 6. 用户常态职责（三流水线共通）

1. 发起：`@generate-knowledge-from-wiki` + 链接，或 `@add-knowledge-from-jira` + `team`，或单独 `@distill-domain-knowledge`（仅 RUNBOOK S2–S7）。
2. **不要**默认自己开终端（Agent 代跑）；凭据在 `.env`：`ATLASSIAN_EMAIL`、`ATLASSIAN_API_TOKEN`。
3. 抽查 `_deliver/` 定稿；业务错误改 **Confluence** 后重跑。
4. 可选：门禁通过后由人手动上传到 Confluence。

---

## 7. 脚本 SSOT（维护者）

| 用途 | 入口 |
|------|------|
| 团队/定稿路径 | `scripts/teams/registry.py` |
| Confluence 同步 | `scripts/sync_domain_knowledge_from_confluence.py`（`scripts/wiki/sync/`） |
| 统一门禁 | `scripts/domain_check.py distill\|jira\|all` |
| Jira 编排 | `scripts/run_jira_knowledge.py` · Ingest：`scripts/run_jira_ingest.py` |
| Confluence 上传 | 人工上传 |
| 历史搬迁 | 不保留归档脚本；一次性迁移完成后删除 |

阅读入口：仓库根 [`TEAM_KNOWLEDGE_BASE.md`](../../TEAM_KNOWLEDGE_BASE.md)。

---

## 8. 单票 Jira 辅助 Skill（非领域库流水线）

与 §3–§4 **并行**，不写 `curated/`：

| Skill | 用途 |
|-------|------|
| `@requirement-risk` | 单票风险可见性报告（对话交付；rule：`requirement_risk`） |
| `@ticket-splitter` | 单票拆单（rule：`ticket_system`） |
| `scripts/jira/attachments/fetch_jira_attachments.py` | MCP 无附件时 REST 落盘 `.jira_attachments/<KEY>/` |

**与领域库联动**：两 Skill 在分析 Jira KEY 时 **默认读取** 领域库落盘，见 [`jira-issue-domain-knowledge-context.md`](jira-issue-domain-knowledge-context.md)。**不**替代 §3–§4 流水线，**不**写入 `curated/`。

索引：[`.cursor/skills/README.md`](../skills/README.md)。凭据可与 §7 共用 `ATLASSIAN_*`。
