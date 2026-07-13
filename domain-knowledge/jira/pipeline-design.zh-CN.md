> English SSOT: [`pipeline-design.md`](./pipeline-design.md).

# Jira 流水线 · 根因与改进（本质）

本文说明旧 Jira 脚本链跑后出现 **「票很多、领域知识很少」** 的根因，以及 Jira 流水线应如何对齐 **统一 Compose** 知识密度目标（S6 源语定稿 → S7 本地语言定稿）。

**现行阶段名**：Ingest → Classify → Recognize（共用）→ Compose（共用 **S3→S7**）。旧 Extract / Integrate 已删除，不再保留审计或兼容入口。见 [`.cursor/skills/add-knowledge-from-jira/RUNBOOK.md`](../../.cursor/skills/add-knowledge-from-jira/RUNBOOK.md)。

---

## 一、根因（本质层）

### 1. 优化目标错位：覆盖率 ≠ 知识密度

| 实际优化 | 应优化 |
|----------|--------|
| 1092 张均有 `raw` + `attribution` | 已确认主题下有 **可争辩的业务规则条文** |
| `check_jira_pipeline` 只验文件存在 | 验 Jira 证据是否通过 S2 closure 进入 S3/S4/S5 |
| 汇报「Classify/Extract/Integrate 完成」却无量 | 汇报「Jira 业务细则是否进入统一 S3/S4/S5 并可核对」 |

**本质**：把 Jira 流水线当成了 **数据管道 / 后补管道**，而不是统一领域知识库的一等证据源。

### 2. 产物层级缺失：只有「地图」，没有「正文」

Wiki Compose 路径明确三层：

```text
materialized/（素材）→ _aggregate/<slug>/（S3）→ _deliver/…工作稿.md（S4/S5）
  → …-source-brief.md（S6）→ …-domain-brief.md / …领域知识定稿.md（S7）
```

Jira 路径曾被压成两层：

```text
raw/ → by-theme/需求归纳.md（Epic 簇 bullet）→ _deliver 文末「Jira 补充（待核）」
```

旧设计试图补一个与 **Compose 定稿同级** 的 Jira 中间层：

```text
jira/by-theme/<theme>/Jira业务规则摘录.md   ← 从长票拆 AC/评论的规则正文
```

**本质**：Classify 默认交付 **索引（index）**，却用 Integrate **附录（appendix）** 冒充 **并入（merge）**。正确修复不是把附录写厚，而是让 Jira business evidence 在 S3 输入层就进入统一 Compose。

### 3. `business_extract` 语义过宽

脚本曾将「主题命中 + 有评论」标为 `business_extract: true`，导致：

- 529 张进入 Extract 筛选，其中大量 **分端重复、纯 Verified、无 AC**；
- 用户预期「600+ 业务票」，实际 **可抽规则的长文** 约 **rich 40% / theme**。

**本质**：**入库队列**（谁可能含规则）与 **蒸馏队列**（谁必须读全文写规则）未分离。

### 4. 与 Confluence 工序不对称

| Confluence（Compose） | Jira（旧） |
|----------------------|------------|
| S4 工作稿写全规则链（源语言） | 簇级摘要 + 少量 KEY |
| 已确认 → S4–S5 | 已确认触发但只做 try 附录 |
| `strategy` 行业模板（资格—分支—后果） | 未强制按模板拆 Ticket AC |

### 5. 渠道 vs 命题（已修，但 Extract 未跟进）

Mall/Hui 不应成为 checklist 行，但 Jira 票 **必须** 在摘录中标注 `product_line`，否则商城/荟 App 规则无法检索。

### 6. `gateway` / `requirements` 不是「未完成的已确认」

二者是 **归属脚本兜底 slug**（映射工程、协作噪声），**不是** 结账/CBP 同级的业务命题。**禁止** 为凑覆盖率对其做 Extract 或升格 checklist「已确认」。含会员可见规则的 CNGW 票应 **`primary` 落在 checkout / contests 等**；纯接口/Session 票保留 `engineering` + `gateway`，进索引即可。

---

## 二、改进原则（第一性）

1. **分轨**：`attribution` = Classify 分诊；`distill_tier/proposition_extract` = S3 证据准入；**真正写规则** 由 Agent 在 S4/S5 基于业务因果合并。  
2. **分三层产物**（已确认主题 mandatory）：

| 层级 | 文件 | 脚本/执行者 | 内容 |
|------|------|-------------|------|
| **索引** | `全量KEY索引.md`、`遗漏扫描.md` | `read_business.py` | 全覆盖、簇、充实票清单 |
| **证据** | `raw/` + `materialized/` + `attribution/` | Ingest/Classify | 正本、可读副本、S3 准入与归属 |
| **并入** | `_aggregate/`、工作稿、定稿 | 统一 Compose | 与 Confluence 一起重组为业务规则链 |

3. **门禁升级**：`domain_check jira --full-raw` 验证备料；`domain_check distill` 验证统一 Compose 后的 S3→S7。  
4. **禁止**用「票数」或旧 Extract/Integrate 完成度汇报成稿；用 `_aggregate/`、工作稿、定稿中的 Jira 业务细则保真度判断。

---

## 四、必要性优先（CBP 32% 的反思 · 第一性）

**错误指标**：`正文引用 KEY 数 / distill_queue 张数` → 驱使「为高而高」扩写附录与分端重复票。

**正确问题**：对顾问/会员可见的 **每条业务命题**，是否同时吸收 **Confluence 宏观规则** 与 **Jira 细则决策（AC/评论 last-wins）**？

| 层次 | 来源 | 回答什么 |
|------|------|----------|
| **政策规则** | Confluence `_deliver` | 资格、周期、阈值、状态机（政策级） |
| **业务细则** | Jira `raw/materialized` + attribution | 页面字段、文案、展示条件、状态分支、AC 与评论决策 |
| **索引** | `遗漏扫描` | 某张分端票是否存在、便于验收追溯 |

**CBP `distill_queue` 188 张的分诊（实测）**

| 类别 | 约张数 | 是否必须进规则正文 |
|------|--------|-------------------|
| 分端实现（iOS/Android/Harmony 同规则） | ~120 | **否** — 1 条命题 + 代表 KEY 即可 |
| Gateway 集成 / 字段映射 | ~22 | **否** — 归工程轨；有 **会员可见后果** 的并入对应命题 |
| 报表 / Downline（非酬宾政策） | ~3 | **否** — 索引或它域 |
| 埋点 / 通知 | 少数 | **否** — 它域或 pass |
| **CBP 核心命题**（Matching/Pacesetter/Milestone/LB…） | **~36** | **是** — 按 **命题簇** 写，不按 120 张分端票堆 |

故 **32% 票级覆盖率可接受**，若 **~10–15 个命题簇** 均已写清且与 Wiki 对齐。偏低的是 **命题级**：核心簇 ~36 张里曾仅显式展开少数代表票，应补的是 **簇合并叙述**，不是再抄 80 张 Harmony 票。

**利用规则（天道）**

1. **Ticket 是证据，不是知识单位** — 知识单位 = **资格—分支—后果** 一条命题。  
2. **last-wins 在评论** — 摘录必须采信晚 Sprint/评论（如 DEV-94875 `qualified`）。  
3. **跨域不重复建域** — 通知、Contest 卡片出现在 CBP 队列时，**引用他域摘录**，不复制全文。  
4. **分诊先于蒸馏** — `distill_queue` 宜再拆：`proposition_core`（必写）/ `platform_variant`（代表 KEY）/ `index_only`（仅索引）。

**改进方向（脚本/Skill，非刷覆盖率）**

- `proposition_extract.py`：按已确认 slug 读取 Confluence closure，同时按 `attribution` 读取 Jira business evidence。  
- 汇报用 `_aggregate/` 中 Jira 来源页、S5 规则链吸收情况、S6/S7 定稿保真度，不用票数比例。  
- Cursor Compose：在 S4/S5 统一重组 Confluence 与 Jira 的条件—分支—后果，避免定稿后附录。

---

## 三、脚本与 Skill 映射

| 阶段 | 脚本 |
|------|------|
| Ingest | `run_jira_ingest.py` · `fetch.py` · `materialize.py` |
| Classify | `attribute.py` · `read_business.py` |
| Unified S3 input | `distill/proposition_extract.py` |

见 [`jira/README.md`](README.md)、[`.cursor/skills/add-knowledge-from-jira/SKILL.md`](../../.cursor/skills/add-knowledge-from-jira/SKILL.md)。
