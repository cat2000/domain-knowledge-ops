> English SSOT: [`first-principles-attribution.md`](./first-principles-attribution.md).

# Jira 归属 · 第一性原理（与 Confluence 归类对齐）

> **Pack 法则 vs 举例：** 下文「primary = 业态轴；渠道 ≠ 领域；sink ≠ 已确认业务」是可复用本质。产品名（商城 / 荟 / 结账 / CBP）仅为**举例**。运行时默认**空表**——词表在 `teams/<team>.json` + checklist（setup 之后）。

## 本质问题

Ticket 归属要回答的是：**这条素材应进入哪条「业务命题」知识链**（与 `DOMAIN_MODULE_CHECKLIST` / `_deliver` 一致），而不是 **在哪个 App 里做**。

| 维度 | 回答的问题 | 落盘字段 | 是否等于「新领域」 |
|------|------------|----------|-------------------|
| **业务命题 `primary` / `themes[]`** | 影响哪类规则（strategy 业态轴） | `primary`, `themes` | **是**（仅清单已有 slug） |
| **渠道 `product_line`** | 实现在哪个 App / 渠道 | `product_line` | **否**（标签，不建 `_deliver/`） |
| **素材类 `material_kind`** | 规范业务 / 映射工程 / 协作噪声 | `material_kind` | **否**（决定 `signal`） |

与 [`strategy.md`](../strategy.md) 一致：一个 Confluence Space 通常是一个限界上下文；产品线父页是 **子树根**，不是与业态轴平级的领域目录。

## `gateway` / `requirements` 不是领域（禁止升格为「确认」）

清单里的 **`gateway`**、**`requirements`** 行是 **Jira 归属兜底 slug** + **Confluence 工程/协作文档目录**，**不是** 与「结账 / CBP / 竞赛」同级的 **业务命题**：

| slug | 实际含义 | 为何不做 `_deliver/` 定稿 |
|------|----------|---------------------------|
| **`gateway`** | CNGW / 接口映射 / Session / Consent 等 **实现层** 工作 | 开发用语；会员可见规则应归 **checkout、contests、messaging…** 等业务命题 |
| **`requirements`** | Grooming、测试工程、Retro、未命中命题的 **协作噪声** | 不是政策/资格/后果链；`signal: pass` 或薄工程票 |

**做法**

- 票上 `primary: gateway|requirements` 只表示 **分诊结果**；若 Ticket 含 **normative AC**，脚本/Cursor 应把 **`primary` 改到业务 slug**（或 `themes[]` 双挂），而不是把整桶升格为已确认。
- Jira business evidence 仅通过已确认主题进入统一 Compose；`gateway`/`requirements` **不算缺口**，与 `非领域` / `facet-unmatched` 同类。
- Confluence 侧 `materialized/by-root/.../facet-gateway/` 可保留 **技术设计素材**；与 **Compose 中文定稿** 分轨。

## 团队配置（命题词表 · Epic · 标题）

| 团队 | 文件 |
|------|------|
| Demo（仓库自带） | [`teams/demo.json`](teams/demo.json) |
| 自有团队 | `teams/<team>.json`，由 [`team-roots.json`](team-roots.json) 挂载 |

`attribute_jira_tickets.py` 通过 `jira_team_attribution.py` 加载：**`facets`** 替代全局撞库；**`epic_primary` / `title_primary`** 优先于关键词；**已确认 slug**（checklist）→ `normative_business` + `distill_queue`。

## 判定顺序（脚本与 Cursor 共用）

1. **协作噪声** → `material_kind: collaboration_noise`，`signal: pass`，`primary: requirements`（或 `gateway` 若纯 CNGW 运维）。
2. **无可见业务后果的工程/映射** → `material_kind: mapping_engineering`，`signal: engineering`，`primary: gateway` 或 `requirements`（**sink，非业务命题**）。
3. **业务命题** → **Epic/标题规则**（`teams/*.json`）→ 再 **facet 关键词**（团队词表）；`themes[]` 可跨域；`primary` 不得长期落在 sink 而票文明显属于某已确认（Cursor B1 纠正）。
4. **`product_line`** → 独立检测 `[Mall]` / `[Hui]` / `CNGW` / `Gateway` 等，**不改变** `primary` 选型。
5. **父级继承** → 子票命题分相同时，可参考 `raw.parent` 摘要；子票 AC/评论可覆盖。

## Recognize · 领域模块确认页（与 Wiki 共用）

- **禁止**因 `[Mall]` / `[Hui]` 票多而新增 `mall-app` / `hui-app` 行。
- **仅当**出现与现有命题 **正交** 的新 **政策/资格/后果链**（且 ≥5 张 Story、Wiki 亦无对应主题）才在「增量主题」加 `初稿`。
- 已有行：更新 Jira 样例与 `product_line` 分布备注（可选）。

## 蒸馏队列 `distill_queue`（与 `business_extract`）

| 字段 | 含义 |
|------|------|
| `substance_chars` / `substance_tier` | 描述+评论总字数；empty/thin/medium/rich |
| `distill_queue` | 主题索引队列 |
| `distill_tier` / `proposition_extract` | 见 [`pipeline-design.md`](pipeline-design.md) §四；S3 只纳入 `proposition_core` / `platform_variant` |
| `business_extract` | 与 `distill_queue` 对齐（D-index） |

**进入 `distill_queue` 条件**（`jira_substance.py`）：`material_kind: normative_business` 且（medium/rich 正文，或 thin+规则样文本，或 Bug/Defect 有结论）。  
**不进入**：纯 Verified 评论、Spike 无 AC、协作噪声、薄工程票。

## 脚本分工（无 LLM）

| 脚本 | 作用 |
|------|------|
| `scripts/jira_substance.py` | 正文字数、`distill_queue` 判定 |
| `scripts/jira_first_principles.py` | 单票归属 |
| `scripts/jira/steps/attribute.py` | `attribution/*.yaml`、`_ticket_attribution.json` |
| `scripts/jira_proposition.py` | `distill_tier`、`proposition_id`、核心命题表 |
| `scripts/distill/proposition_extract.py` | S3：按 S2 closure 把已授权的 Jira business evidence 纳入统一命题候选 |
| `scripts/jira/steps/read_business.py` | Classify 索引：全量 KEY 索引、遗漏扫描 |
| `scripts/jira/steps/check_pipeline.py` | `--full-raw` 备料完整性检查 |

**Cursor**：统一 Compose（**S3→S7**）中完成语义合并；见 [`pipeline-design.md`](pipeline-design.md)。
