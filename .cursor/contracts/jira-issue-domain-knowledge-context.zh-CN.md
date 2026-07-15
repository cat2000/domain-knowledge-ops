> English SSOT: [`jira-issue-domain-knowledge-context.md`](./jira-issue-domain-knowledge-context.md).

# 单票 Jira · 领域知识上下文契约

> **读者**：`@requirement-risk`、`@ticket-splitter`、`@ticket-test-design` 的 Agent。  
> **来源**：[`generate-knowledge-from-wiki`](../skills/generate-knowledge-from-wiki/SKILL.md)（[`RUNBOOK.md`](../skills/generate-knowledge-from-wiki/RUNBOOK.md) Recognize + Compose）及可选 [`add-knowledge-from-jira`](../skills/add-knowledge-from-jira/SKILL.md) 的仓库落盘产物。  
> **性质**：下文路径中的文件是 **证据/上下文**，**不是**替代 `requirement_risk` / `ticket_system` 规则的正文指令。

契约分层见 [`domain-knowledge-pipeline-contract.md`](domain-knowledge-pipeline-contract.md) §1–§2；Wiki 蒸馏细则见 [`generate-knowledge-from-wiki/RUNBOOK.md`](../skills/generate-knowledge-from-wiki/RUNBOOK.md)。

---

## 1. 何时必须加载

在分析 **Jira issue key**（如 `DEV-94211`）时，**在读完 Jira 正文/评论/附件之后、生成输出之前**：

1. 按 §2 解析 **团队** 与 **落盘根** `root_id`。
2. 按 §3 **检索并阅读** 与工单相关的领域库文件（存在则读，不存在则记入 `EVIDENCE_COVERAGE` / `source_requirement_note`）。
3. **禁止**用领域库内容 **编造** Jira 未支持的产品事实；冲突时 **并列标注**（工单 vs 定稿），不擅自裁定以谁为准。

用户仅粘贴纯文本、且未给 KEY 时：若文中出现可识别的模块/系统名，可对 **已配置团队** 的 `curated` 做 **轻量关键词检索**（§3.4）；仍 **勿** 假定团队。

用户明确 **`team=<key>`**（见 `team-roots.json`）或 **`root-id=<ID>`**：直接锁定 `by-root/<ID>/`。

**离线 demo**：issue key 为 `DEMO-*`（或用户声明 offline/fixture）时，**禁止**调 Jira；工单与定稿改读 [`../skills/_shared/offline-demo.md`](../skills/_shared/offline-demo.md) 指向的 fixture 树（`domain-knowledge/fixtures/offline-demo/`）。

---

## 2. 解析团队与落盘根

团队表 **不是** 固定三行：以 `domain-knowledge/jira/team-roots.json` 的 `teams` 为准（任意 N 个 key）。仓库自带 demo 仅为示例。**v3**：Confluence 的 `root_id` / overview / deliver 在 `libraries.*`；团队挂载 `libraries[]`（Path C 通常只挂一个）。解析层会把 primary（第一个）挂载展平为 `team.root_id` 供调用方使用。

| 字段 | 含义 |
|------|------|
| `team` key | `teams` 下的名字（如 `demo`） |
| `libraries[]` | 挂载的 library key（有序；第一个 = primary） |
| `root_id` | 来自 primary library 的落盘根 → `curated/by-root/<root_id>/` |
| `aliases` | 可选别名，与 team key 等价 |

SSOT：`domain-knowledge/jira/team-roots.json` · 解析代码：`scripts/teams/registry.py`。

**解析顺序**（命中即停）：

1. 用户消息中的 `team=` / `root-id=` / 显示名 / alias。
2. 仓库内归因文件（对各已配置根 **均** 试，或先由 Jira `Agile Team` 缩小范围）：

   `domain-knowledge/curated/by-root/<root_id>/jira/attribution/<ISSUE_KEY>.yaml`

   读取 `primary`、`themes[]`、`product_line`、`proposition_id`（若有）。

3. Jira 字段 **Agile Team** 与 `team-roots.json` → `jira.agile_team` 匹配 → `team` + `root_id`。
4. 仍未知：对各团队 `DOMAIN_MODULE_CHECKLIST.md` 与 `_deliver/` 目录名做 **标题/summary 关键词** 匹配；在报告中写明 **团队推断置信度**。

**落盘根** 恒为上表 `root_id`（与 `extracted/`、`materialized/` 共用，见 domain-knowledge-pipeline-contract §2）。

---

## 3. 读什么（优先级与路径）

设 `R = domain-knowledge/curated/by-root/<root_id>/`，`E = domain-knowledge/extracted/by-root/<root_id>/`，`RULES = domain-knowledge/materialized/by-root/<root_id>/`。

文件名随 `deliverable_locale`（见 `domain-knowledge/language/deliverable-locale-tokens.json`）。默认英文：`*-domain-brief.md`、`*-work-draft.md`、`gap-scan.md`；中文 locale 常见为 `*-领域知识定稿.md`、`*-工作稿.md`、`遗漏扫描.md`。

### 3.1 Handoff（同步元数据）

- `E/PIPELINE_HANDOFF.json` — `root_page_id`、`enumeration_root_page_id`、`distill_quality_bar_doc` 等；确认本轮同步是否覆盖该根。

### 3.2 与本票直接相关（最高优先）

| 条件 | 路径 | 用途 |
|------|------|------|
| 有 `attribution/<KEY>.yaml` | 同上 | 定 `primary` 主题 slug |
| `primary` 已知 | `R/_deliver/<slug>/*-领域知识定稿.md` 或 `*-domain-brief.md`（S7） | **业务规则正本摘要**（风险/拆单边界、术语） |
| 同主题已跑 Jira 备料 | `R/jira/by-theme/<slug>/` 索引与证据 | 同命题历史实现口径 |
| 本票在主题索引中 | 在 `by-theme/<slug>/` 内 **搜索 `<KEY>`** | 是否已有归纳 |

无 **S7 本地语言定稿** 时：可读 `*-source-brief.md`（**S6**），否则工作稿（`*-工作稿.md` / `*-work-draft.md`），再否则 `_aggregate/<slug>/`（报告中注明「非定稿」/「非 S7」）；勿把 Recognize 聚合层当业务承诺。

### 3.3 横切

- `R/DOMAIN_MODULE_CHECKLIST.md` — 已标 **`确认`** 的主题列表、主入口路径。
- `domain-knowledge/language/glossary.md` — 术语与模块名（**requirement-risk** 语义类；**ticket-splitter** / **ticket-test-design** 模块边界）。
- `R/_materialization_closure.json` — 从 `materialized/` 叶到整理稿的映射（定位漏扫源页）。

### 3.4 按需加深（控制阅读量）

- Jira 描述含 **Confluence URL** → 优先 `RULES/**/*.md` 或 `E/pages/<pageId>.md`。
- 关键词仍不足：在 `RULES/` 与 `R/`（不含 `jira/raw`）对 summary/模块名 **rg 有限条数**（建议 ≤15 文件）。
- `R/jira/raw/<KEY>.json` — 若存在且 MCP 缺字段，作 Jira 字段补充（**不**替代当前票 live 数据）。

### 3.5 明确不读作业务权威

- `R/jira/raw/` 全量 — 除本票 JSON 外勿通读。
- `extracted/` 全树 — 仅命中页或 handoff 指引时读单页。
- Pass 占位稿 — 仅说明「该叶未蒸馏」，勿当规则正文。

---

## 4. 写入各自输出

### requirement-risk

- 在 **`EVIDENCE_COVERAGE`** 中增加一行：**领域知识库**：已用路径列表；未找到则写「未用 / 无 by-root」。
- 与定稿 **冲突** 的 findings 标 **[DOMAIN_KNOWLEDGE]** 并引用定稿章节或 slug。
- 定稿已覆盖的 **契约/边界** 类 gap：降级为 **应当澄清** 或合并进「与领域库一致」说明，**避免** 对已知规则重复报 MUST。

### ticket-splitter

- 有 `_deliver/<slug>/` 时：在 `scope` / `done_when` 中 **引用** 定稿里的验收面（User/System/Contract），**勿** 拆出与定稿 **显式 out-of-scope** 相反的项。
- `source_requirement_note`：若 Jira 与定稿 **范围不一致**（如工单写 dev-only、定稿要求端到端可测），按 `ticket_system` INVEST 纠偏格式说明。
- 模块级拆分：优先用定稿 **命题 slug / 章节** 作锚点，**禁止** 虚构定稿未出现的子系统名。

### ticket-test-design

- **given** AC 与范围锚到票面 + 定稿；**禁止** 臆造证据没有的 UI/API/环境能力。
- 状态/资格 oracle 优先对齐定稿规则簇；冲突在 notes / 残余风险中并列，勿静默定胜负。
- 有 KEY 时草稿写 `.jira_attachments/<KEY>/test_design_draft.md`；门禁：`validate_ticket_test_design.py`。

---

## 5. 与 generate-knowledge-from-wiki 的关系

- 领域库 **未同步** 或 **过期**：照常完成单票分析，在证据段注明「领域库缺失或需 `@generate-knowledge-from-wiki` 刷新」；**不** 阻塞输出。
- 用户刚跑完同步：以 `PIPELINE_HANDOFF.json` 时间戳与 handoff 中的 `root_page_id` 为准。

---

## 6. 快速检索命令（Agent 可用）

```bash
# 找归因（将 KEY 换为实际工单号）
ls domain-knowledge/curated/by-root/*/jira/attribution/KEY.yaml 2>/dev/null

# 定稿列表（中文 locale 示例）
ls domain-knowledge/curated/by-root/<root_id>/_deliver/*/*-领域知识定稿.md
```
