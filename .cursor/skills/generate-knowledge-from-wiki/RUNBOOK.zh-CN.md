# generate-knowledge-from-wiki · 执行剧本（Agent 必读）

> English SSOT: [`RUNBOOK.md`](./RUNBOOK.md).
>
> **读者**：Cursor Agent（**S1** 完成后 **必须** 读本文件）。  
> **入口**：[`SKILL.md`](./SKILL.md) · **脚本**：[`S1-SYNC-CLI.md`](./S1-SYNC-CLI.md)  
> **契约**：[`../../contracts/domain-knowledge-pipeline-contract.md`](../../contracts/domain-knowledge-pipeline-contract.md) §1–§2 · **质量栏**：`domain-knowledge/distill-quality-bar.md`

---

## 三阶段总览（主叙事）

Confluence 管线对外用 **三阶段**；**S1–S6** 为 Agent **操作编号**（门禁、产物路径、汇报仍用 S*）。

| 阶段 | 含义 | 对应步 | 执行者 | 停闸 |
|------|------|--------|--------|------|
| **Ingest**（摄入） | 同步 + facet 物化（**机器粗分**） | **S1** | 脚本 | — |
| **Recognize**（认域） | 命题级认域 + closure + 人 **`确认`** | **S2** | 脚本（Agent 审阅） | **备料末：停** |
| **Compose**（成稿） | 归集 → 领域模型 → 工作稿 → 中文定稿 | **S3 → S4 → S5 → S6** | S3=脚本；S4/S5/S6=Agent | 仅 **`确认`** 行 |

- **备料** = **Ingest + Recognize**（S1 + S2）→ **暂停**（人审确认页）  
- **成稿** = **Compose**（S3 → S4 → S5 → S6；用户 **`继续`** 后，可按 slug 分批）

Compose 四子步：**S3 归集**（保真分轨、索引与可验证传递，不做翻译或业务裁决）→ **S4 领域模型**（对象/状态/动作/关系建模，不翻译）→ **S5 工作稿**（基于模型挂载规则链，不翻译）→ **S6 定稿**（仅中文表达转换，对外承诺）。

---

## 六步操作编号（S1–S6）

| 步 | 阶段 | 名称 | 执行者 | 产物 | 语言 |
|----|------|------|--------|------|------|
| **S1** | Ingest | 同步 | 脚本 | `extracted/`、`materialized/` | 原文 |
| **S2** | Recognize | 认域·打标 | 脚本（Agent 审阅） | **领域模块确认页**、`_materialization_closure.json` | 不改写 |
| **S3** | Compose | 归集 | 脚本 | `_aggregate/<slug>/` | 原文 |
| **S4** | Compose | 领域模型 | Agent | `_deliver/…-工作稿.md` 的 `## 领域模型` | 与源一致 |
| **S5** | Compose | 工作稿 | Agent | `_deliver/…-工作稿.md` | 与源一致 |
| **S6** | Compose | 定稿 | Agent | `_deliver/…-领域知识定稿.md` | **简体中文** |

### 职责边界（Skill vs Script）

| 步 | Skill/Agent 主责 | Script 主责 |
|---|---|---|
| S1 | 契约：输入边界、禁翻译、禁语义改写 | 执行：同步、物化、粗分 |
| S2 | 契约：确认语义、人工闸门、审阅动作 | 执行：识别、closure、账本、阻断 |
| S3 | 契约：保真分轨、延迟裁决、决策契约字段 | 执行：抽取、标准化、索引、最小审计视图 |
| S4 | 契约：领域模型（对象/状态/动作/关系/容器/字段锚点） | 执行：模型结构门禁，不生成正文 |
| S5 | 契约：模型挂载后的规则链、冲突显式化 | 执行：工作稿质量门禁，不生成正文 |
| S6 | 契约：表达转换边界、承诺结构 | 执行：门禁、回归、报告 |

边界规则：
- Script 只做确定性处理，不做业务规则裁决。
- Script 不做 S4/S5/S6 文本模板兜底，缺稿必须显式失败。
- Agent 负责裁决与叙事，不以手工 patch 替代流程性修复。

### 旧路径废弃（必须执行）

- 废弃 `S6 -> decision_atoms -> S5/S4` 反向依赖，S3 是结构化证据源，不是业务裁决源。
- 废弃 Compose 编排器中 `WORK_DRAFTS` / `FINAL_DRAFTS` 自动填充主路径。
- 如 S4/S5/S6 文件缺失，编排器必须报错并停止，不允许脚本代写正文。

### S1 与 S2 分工（勿把两步当成重复认域）

| | **S1 · 同步** | **S2 · 认域·打标** |
|---|----------------|---------------------|
| **本质** | **机器粗分**（脚本、无 LLM） | **命题级认域 + 闭环 + 人确认** |
| **做什么** | REST 抽取；`facet_classify` 按标题/摘要关键词写入 `facet-*/` | 用统一 source registry 做命题级认域：Confluence 读 S1 manifest/materialized，Jira 读 attribution；刷新确认页与 closure；上一轮 `glossary.md` 仅作轻量同义词参考 |
| **产物** | `extracted/`、`materialized/by-root/<R>/facet-*/` | `DOMAIN_MODULE_CHECKLIST.md`、`_materialization_closure.json` |
| **不算完成** | `facet-*` **≠** 已确认领域块；**≠** 定稿 | 清单标 **`确认`** **≠** 已有中文定稿 |

S1 的 `facet-checkout/` 等是 **物化目录启发式**，不是 checklist 里的 **确认 slug**。S2 **必须**显式打标 closure，且 **不得**仅凭 facet 目录名报「模块已覆盖」（见 §S2 禁止项）。

### 成稿目标函数（S4–S6 · 优先序）

执行 **S4 / S5 / S6** 时以 [`distill-quality-bar.md`](../../../domain-knowledge/distill-quality-bar.md) **§目标函数** 为裁判（细则与同文件 §落稿前分流、§禁止项 一并适用）：

1. **领域模型化** — 先识别领域对象、状态、动作、状态变化、展示容器、字段锚点，再挂载规则链；**错误**目标是直接堆规则清单。
2. **业务噪声隔离** — 协作排期、纯工单矩阵、DDL/SQL/Git、无业务解释的字段海 → 从主决策链分流为支撑材料/噪声，不让它们冒充业务规则。
3. **全面（业务侧）** — 凡影响「该不该、会不会对用户/顾问产生可见后果」的条文 **写全、可核对**；合并重复，**禁止**用「详见 materialized」代替整条规则链。
4. **语言** — **S4/S5 不翻译**；**仅 S6** 产出读者向简体中文。

- **领域模块确认页** = `DOMAIN_MODULE_CHECKLIST.md`；**「状态」= `确认`** 授权 **成稿**。
- **`确认` ≠ 已定稿**；定稿完成 = 已有 **S6** `…-领域知识定稿.md`。
- **禁止**仓库 HTTP LLM API；**S1–S5 禁止**全文翻译。
- 默认 `@generate-knowledge-from-wiki` = **备料**（Ingest→Recognize / S1→S2）→ **暂停**；标 **`确认`** 后 **`继续`** 跑 **Compose**（S3→S6，可按 slug 分批）。
- **落盘根**：`extracted/by-root/<R>/PIPELINE_HANDOFF.json` → `root_page_id`。

---

## S1 · 同步（脚本 · 机器粗分）

脚本内：`extract` → `facet_classify` → `materialize`。产出 **忠实原文** + **`facet-*` 目录**（关键词启发式，供 S2 扫描，**非**命题终稿）。

S1 默认必须完整：`_last_extract_report.json` 中只要有 page error，就停止在 S1，不写 complete handoff，也不进入 S2。只有人工明确接受缺页风险时，才可加 `--allow-partial` 写出 `s1_status=partial` 的 handoff。

S1 物化必须以当前 source set 为准：`materialized/by-root/<R>/_materialized_manifest.json` 是生成清单，物化时会删除不再由当前抽取页产生的旧 `.md`，避免旧素材污染 S2。

S1 粗分只执行 profile 配置：facet 关键词与显式噪声标题来自 `domain-knowledge/s2-domain-profiles.json`，脚本不得内置团队或历史页面特例。

**Strategy-first**：若 `checklist_themes` 为空，**硬停**——先 `@setup-domain-ops` 填实 [`strategy.md`](../../../domain-knowledge/strategy.md) §2 并派生 profiles，再跑 S1/S2。空壳仓库不提供业态默认模块。

```bash
python3 scripts/sync_domain_knowledge_from_confluence.py --url "<PAGE_URL_OR_ID>"
```

1. 代跑；读 **HANDOFF** → 落盘根 `<R>`。
2. 否则进入 **S2**（命题级认域，见上表）。

参数与排障见 [`S1-SYNC-CLI.md`](./S1-SYNC-CLI.md)。

---

## S2 · 认域 + 全库打标（备料末步 · 命题级）

**目的**：在 S1 粗分和 Jira Classify 之上，认全 **领域命题块**；每个参与验收的 source 在 closure 中有落点；刷新 **领域模块确认页** 并等人标 **`确认`**。

**前置**：`s2-domain-profiles.json` 的 `checklist_themes` 须已由 strategy 派生且人确认；否则硬停并转 `@setup-domain-ops`。

**首次认域 / 换团队根 / 模块表过粗时 / S1 重扫后页数显著变化时**，可先跑 **模块提议**（路径 B）辅助人审，再更新 profile、再 recognize：

```bash
# team 由 root-id 在 team-roots.json 中解析；module_seeds 按 teams[] 过滤（可为空，则仅靠 Wiki 树，须更强人审）
python3 scripts/distill/s2_propose_modules.py --root-id <R> --write-checklist-draft
```

- 读 Confluence **Wiki 树**（REST BFS，需 `.env` 凭证）+ **`s2-propose-industry-seeds.json`**（由 `strategy.md` §2 派生；开源默认可为空）+ S1 facet/标题
- 产出 **`S2_PROPOSED_MODULES.json`**、**`S2_PROPOSED_MODULES.md`**（及可选 **`DOMAIN_MODULE_CHECKLIST.proposed.md`**，状态均为 **`待确认`**）
- **人审**后把确认的 slug/cues 写入 **`s2-domain-profiles.json`**（根 profile 或 `profiles_by_team.<team>`），须与 `strategy.md` §2 一致，再跑下方 recognize

S2 recognize（在 profile 就绪后）：

```bash
python3 scripts/distill/s2_recognize.py --root-id <R>
```

该脚本会输出：
- `DOMAIN_MODULE_CHECKLIST.md`
- `_materialization_closure.json`
- `_附录/非业务/非业务资料索引.md`
- `S2_DECISION_LEDGER.json`（机器识别账本）
- `S2_REVIEW_DECISIONS.json`（人工裁定账本）
- `S2_RECALL_REVIEW.md`（疑似漏识别清单，供人工确认）

| 动作 | 产出 |
|------|------|
| `strategy.md` **领域命题标尺** × 统一 source registry | `curated/…/DOMAIN_MODULE_CHECKLIST.md` |
| Confluence：读取 `materialized/by-root/<R>/_materialized_manifest.json`（缺失时 fallback 扫描 materialized） | `curated/…/_materialization_closure.json` |
| Jira：读取 `jira/attribution/*.yaml` / `_ticket_attribution.json`，按 `primary/themes[]/distill_tier` 映射 | 同上 closure + 确认页（**索引路径**，禁止多目录贴全文） |
| 非业务页 | 占位 + `## 非业务判定（Cursor）`；**不进成稿** |

**禁止**：全文翻译；在多个产出目录中 **重复粘贴** 同一段 `materialized/` 原文；将 S1 的 **`facet-*` 目录名**（如 `facet-checkout/`、`facet-unmatched/`）当作领域命题 slug。

**分散素材防漏**：Confluence 侧除按 `strategy.md` 命题归类 `materialized/` 外，还须对 `materialized/` 做全文检索与语义补漏；Jira 侧不重新全文扫文件认域，而以 Classify attribution 为 source registry，必要时由 Agent 修正 YAML。补漏路径写入 `_materialization_closure.json` 与 **领域模块确认页**。上一轮稳定 `glossary.md` 仅可作为同义词/缩写提示，不得依赖其完备性决定领域边界；本轮新发现术语只写入确认页 **术语备注**，待 S6 后沉淀进术语表。

**primary facet 复核**：S1 `facet-*` 只是粗分默认值，不是领域 slug 的最终裁决。即使命中 `primary_facet_to_slug`，S2 仍必须用页面标题/路径级 `route_overrides` 做跨 slug 复核；只有标题/路径明确指向其它 confirmed slug 时才改派，正文偶发词不得触发跨 slug 转交。

确认页规则：[`domain-module-checklist.mdc`](../../rules/domain-module-checklist.mdc) · 版式：[`DOMAIN_MODULE_CHECKLIST.template.md`](../../../domain-knowledge/DOMAIN_MODULE_CHECKLIST.template.md)。

**备料完成汇报**：确认页 + closure 齐；**尚无** `_aggregate` / 定稿。然后 **必做**：

```bash
python3 scripts/distill/tagging_acceptance.py --root-id <R>
```

向人展示 `TAGGING_ACCEPTANCE.md`。**暂停** → 仅对报告允许的行标 **`确认`**。**禁止**引导「全部确认」。

若已配置 `board_id` 且报告显示 Jira attribution = 0，建议先 `@add-knowledge-from-jira team=<key>`，再重跑 S2 + 打标验收。

**S2 后门禁（建议）**：`python3 scripts/distill/coverage.py --root-id <R>`

**Compose 硬门禁**：满足以下任一条件，`proposition_extract.py` 默认阻断 S3（需显式 `--allow-unconfirmed` 才可越过）：
- `DOMAIN_MODULE_CHECKLIST.md` 仍有 `待确认`

---

## 人工闸门 · 领域模块确认

| 动作 | 说明 |
|------|------|
| 人编辑确认页 | 认可行 **「状态」** → **`确认`**（仅当打标验收允许；零来源保持 **待确认**） |
| **`继续`** | 对 **`确认` 行** 跑 **S3→S7**（可限定 slug） |
| 尚无 **`确认`** | **不** 跑 S3 / S4 / S5 / S6 |

**空证据**：备注 / 打标报告写明无 tagged 来源（或 S3 后 `pages_with_props=0`）时 **禁止**标 **确认**。

**低证据**：仅在有意时确认；S7 顶部必须有 **证据不足** 横幅，缺口写入待确认；risk 在 `EVIDENCE_COVERAGE` 中按非 SSOT 处理。

**零规则假覆盖禁止**：已确认且有来源，但 S7 无任何 `### 规则` → 改回 **待确认** 或重写。

**保持业态裁决轴**：产品面密页重挂载入现有轴（见 `industry-axis-remount.md`）；默认不重建 Mall/惠/Gateway/Messaging 模块。

重扫时 **增量合并**；**保留**人手 **`确认`**。S2 按状态 + 来源数刷新 **备注**（确认后清除过时的「等待人工确认」）。

---

## Compose（成稿）· S3 → S6（仅 **`确认`** 主题）

### S3 · 归集（Compose ①）

| 产出 | 规则 |
|------|------|
| `_aggregate/<slug>/` | 对已确认模块做保真分轨、溯源索引与结构化传递，保留原文语言；不做读者向改写或业务裁决 |

S3.5（新增，脚本化命题中间层）：

- 先运行 `python3 scripts/distill/proposition_extract.py --root-id <R>`（可 `--only-slug`）
- 产物：
  - `_aggregate/<slug>/<slug>-propositions.json`（逐页候选命题结构化）
  - `_aggregate/<slug>/<slug>-命题清单.md`（人工/Agent 可审稿）
  - `_aggregate/CROSS_SLUG_HANDOFF.json|md`（S2 primary facet 跨 slug 转交审计清单；无转交时仍生成空清单）
- source set：只读取 S2 `_materialization_closure.json` 中指向已确认 slug 的 source；Confluence 路径解析到 `materialized/by-root/<R>/`，Jira 路径解析到 `curated/by-root/<R>/jira/materialized/`；S3 禁止重新按 `facet-*`、Jira attribution 或目录扫描决定准入。
- 约束：S4/S5 应优先消费该命题清单，而不是直接复写页面摘要。
- cross-slug 约束：S4/S5 必须检查 `_aggregate/CROSS_SLUG_HANDOFF.md`；目标 slug 对转交页面必须明确吸收、降层或排除，不得因为页面原本位于其它 `facet-*` 目录而静默丢失。
- 要求：每条 `proposition_item` 应尽量产出 `decision_block`（对象/条件/动作/后果/阈值/时间窗/例外）与 `decision_confidence`，供 S4 建模与 S5 挂载规则链。
- 保真分轨契约（必须）：
  - 页面级：`doc_intent`（`rule_spec` / `api_contract` / `release_change` / `test_ops` / `discussion_decision`）
  - 页面级：`structured_source`，当 S1 有长映射表、字段表、状态枚举表、资格/等级/奖励档位表、时间窗表或可见文案表时，必须记录结构信号、表头/字段、密集行数量和样例行；这不是业务裁决，只是防止长表因单行命题弱而丢失
  - 命题级：`candidate_type`（`contract_candidate` / `evidence_note` / `noise_context`）+ `eligibility_reason`
  - 保真级：`semantic_roles` / `semantic_preservation_reason` / `business_scope_label`
  - 证据级：`scope_id` / `scope_label` + `evidence_span`
  - 编排级：`decision-atoms` 仅消费 `contract_candidate`，且只作为最小审计视图；`evidence_note` 保留为 S4 延迟裁决证据；`noise_context` 默认不进入 S4 重挂载
- 因果优先契约（新增）：
  - 命题级必须补充 `decision_track`（`decision_core` / `presentation_context` / `unresolved_critical` / `noise_context`）
  - 命题级必须补充 `causality_score`（用于“可决策因果”优先排序）
  - `unresolved_critical` 代表高价值但待裁决项，禁止在 S4/S5/S6 被弱化或吞并
  - S3 禁止根据阈值大小、局部样例或隐含业务知识推断分支；只保留源材料显式结构，业务含义由 S4/S5 Agent 重挂载
- 单阶段准入：
  - 仅按 `decision_track + causality_score + signal + fields` 判定是否进入 `contract_candidate`
  - `presentation_context` 进入 `evidence_note` 延迟裁决；`noise_context` 写 `admission_drop_reason` 后隔离
  - 文档类型（`doc_intent`）只作为阈值先验，**不能**直接否决高因果命题
- 高置信触发门禁（避免误杀）：
  - `proposition_quality` 对 `doc_intent/candidate_type` 做硬校验（字段合法性、一致性、缺失）
  - 意图分流比例门禁只在“标题强匹配 + 样本量足够”时触发硬失败（如 release 页面契约泄漏过高）
  - 禁止直接把启发式 `doc_intent` 误差放大为全链路失败

**重挂载（保持业态裁决轴）**：归集时将 Mall/惠/结账/竞赛/身份等产品面页挂入已确认业态 slug —— 见 [`references/industry-axis-remount.md`](./references/industry-axis-remount.md)。默认不重建这些为模块。

**S3 后（起草 S6/S7 前必做）**：

```bash
python3 scripts/distill/tagging_acceptance.py --root-id <R> --after-s3
```

对照 closure / `pages_with_props` /（随后）S7 规则数。写尽不足 → 重挂载残留证据或待确认；不得声称「已齐」。`pages_with_props=0` → 不得交付已确认 S7。

S3.6（最小派生审计视图）：

- 运行 `python3 scripts/distill/decision_atom_sync.py --root-id <R>`
  - 产物：`_aggregate/<slug>/<slug>-decision-atoms.json|md`
  - 作用：从 `contract_candidate` 生成最小核对视图（对象/条件/分支/后果/时间窗/例外/证据），不替代 S4 领域模型或 S5 语义重挂载
- 运行 `python3 scripts/distill/conflict_ledger_sync.py --root-id <R>`
  - 产物：`_aggregate/<slug>/<slug>-conflict-ledger.md`
  - 作用：把冲突显式化（已裁决 / 待确认），禁止正文静默覆盖口径

Pass / 非领域 **不做 S3**。

### S4 · 领域模型（Compose ②）

| 产出 | 规则 |
|------|------|
| `_deliver/<slug>/<slug>-领域知识-工作稿.md` 的 `## 领域模型` | 识别领域对象、状态/阶段、业务动作、状态变化、展示容器、字段锚点；**不翻译** |

S4 领域模型最低要求（供 S5 继承）：

- 明确 **一等业务对象**：业务对象，不是页面/API/字段/指标/边界材料。
- 明确 **指标/字段**：公式、进度、金额、目标、API 字段、枚举值等可度量或承载字段。
- 明确 **展示容器**：卡片、列表、详情页、页面区域、API 响应等承载层。
- 明确 **对象关系**：对象之间的依赖、承载、计算、展示、钻取或前置关系。
- 明确 **状态机/状态转换**：核心对象从什么状态到什么状态，或资格/金额/展示如何变化。
- 明确 **边界候选**：排除材料、待迁移主题、发布/合规/工程支撑等，不得混入一等业务对象。

S4 输出结构（强制）：

- `## 领域模型`：按 `一等业务对象`、`指标/字段`、`展示容器`、`对象关系`、`状态机/状态转换`、`边界候选` 分层列出。
- UI/API/字段/指标/公式只能落在 `指标/字段` 或 `展示容器`，不得作为一等业务对象。
- 若某个高价值 evidence 无法挂到任何领域对象，必须在 S5 待裁决中说明 `关联前置域` 与 `决策影响`。

S4 MUST（Skill 主定义，脚本仅验证）：

- Agent 必须先读 `_aggregate/<slug>/<slug>-propositions.json` 与 `*-命题清单.md`；`decision-atoms` 只能辅助核对，禁止作为生成主源。
- Agent 必须先按 `strategy.md` / `distill-quality-bar.md` 判断源材料中的一等业务对象：对象、条件、业务分支、状态/阶段/等级、资格、奖励、展示规则、阈值、时间窗、用户可见影响。
- 命名业务结构必须保留：源材料中的命名分支、阶段、路径、档位、等级、状态、周期、市场、卡片等，只要承担业务判定或可见后果含义，就必须进入主链或待裁决区，不得抽象成无名条件后消失。
- Agent 必须把页面、接口、字段、卡片、弹窗、列表降层为证据位置、字段锚点或展示容器。
- Agent 必须用模型先解释“这个领域由哪些对象和状态组成”，再让 S5 写规则链；禁止直接从来源小节堆链。
- 脚本门禁：`python3 scripts/distill/domain_model_quality.py --root-id <R>` 只验证模型结构、S5 链对象是否继承 S4 一等业务对象、字段/API/页面是否被降层；不得生成或替代 S4 语义正文。

### S5 · 工作稿（Compose ③）

| 产出 | 规则 |
|------|------|
| `_deliver/<slug>/<slug>-领域知识-工作稿.md` | 基于 S4 领域模型挂载规则链、冲突显式化、业务写全（目标函数 1–3）；**不翻译** |

S5/S6 落稿前必须先读 [`domain-knowledge/distill-authoring-contract.md`](../../../domain-knowledge/distill-authoring-contract.md)。该文件定义可通过门禁的最小作者契约；本 RUNBOOK 定义语义原则与流程。

S5 每条规则链最低要求：

- `领域对象`：必须来自 `## 领域模型` 的 `一等业务对象`
- `状态变化`
- `业务动作`
- `展示容器/字段锚点`：只能引用模型中的 `指标/字段` 或 `展示容器`
- 明确 **适用对象**（谁）
- 明确 **触发条件**（何时生效，含阈值/时间窗/状态）
- 明确 **分支或动作**（怎么处理）
- 明确 **用户可见影响**（对用户/顾问产生什么可见影响）
- 至少 1 个 **具体锚点**：数值、状态迁移、API/字段 token、时间窗、枚举值之一

S5 输出结构（强制）：

- `## 概述与范围`：用业务语言说明本稿覆盖的领域对象、范围和读者问题；S5 已是领域知识工作稿，不得只有输入处置和链表。
- `## 输入处置摘要`：说明本稿如何处置 `contract_candidate` / `evidence_note` / `noise_context`；必须单列 high-value evidence（公式、阈值、状态枚举、展示映射、卡片可见性、时间窗、资格/奖励/金额后果、用户可见字段）的处置：进入闭环、半闭环拆分、待裁决或排除原因
- `## 领域模型`：承接 S4 分层模型；每条闭环链必须挂到其中的一等业务对象，并可引用指标/字段与展示容器。
- `## 组织顺序说明`：在闭环链之前，按最终落稿顺序逐条写 `链 N：标题 — 顺序理由`；用于证明 S5 已把来源顺序/API 顺序/UI 顺序转为业务判定顺序
- `## 已闭环决策链`：仅承接 `decision_track=decision_core` 的规则簇
- `## 待裁决关键问题`：承接 `decision_track=unresolved_critical`，逐条写“关联链/关联前置域/待裁决点/当前证据/待确认事项/决策影响”
- `## 结构化明细转交`（条件性）：当 S3 proposition、S3 页面级 `structured_source` 或 S5 语义重挂载发现映射表、状态枚举、字段清单、公式/阈值表、时间窗表、可见文案清单、编号/档位/等级映射时必须出现；先按“三分法”裁定完整展开、规则化压缩或待确认，再按业务规则分 `###` 小节，用表格或缩进列表保留可查询明细，作为 S6 `## 关键明细` 的唯一来源
- `presentation_context` 仅作支撑信息，不得冒充主决策链
- 交付/协作/验收节奏材料（如体验版、bug list、sprint/retro、代码提交频率、三方协作、阶段验收日期）默认是边界或支撑证据；只有当它直接改变业务对象的用户可见承诺时，才能写入闭环链，并且必须把交付语境降层为展示/质量影响。
- 半闭环材料必须拆分：已明确业务规则写入闭环链，未明确实现/API/字段/检测方式写入待裁决区；闭环链必须写 `关联待裁决：问题 N`。
- 输入处置摘要必须说明重复/跨 UI 容器/跨 API 字段的语义归一结果：合并为主规则、降为字段锚点、列为展示位置、或进入待裁决。
- 输入处置摘要只说明顺序归一原则，不另写一套详细链序；详细链序只以 `## 组织顺序说明` 为准，避免全稿出现两个顺序真相。

S5 MUST（Skill 主定义，脚本仅验证）：

- Agent 必须先读 S4 领域模型、`_aggregate/<slug>/<slug>-propositions.json` 与 `*-命题清单.md`；`decision-atoms` 只能辅助核对，禁止作为生成主源。
- Agent 必须逐类处置 `contract_candidate` / `evidence_note` / `noise_context`：进入闭环链、进入待裁决、作为支撑证据、或排除为噪声。
- Agent 必须做 high-value evidence uplift scan：凡 evidence 中含公式、阈值、状态枚举、展示映射、卡片可见性、时间窗、资格/奖励/金额后果、用户可见字段，即使不是 `contract_candidate`，也必须被提升为闭环链、半闭环链或待裁决问题；禁止仅因 S3 未收为 contract 就降级为支撑材料。
- Agent 必须做结构化明细转交：凡 high-value evidence 或页面级 `structured_source` 中的表格、枚举、字段列表、编号映射、状态窗口、阈值/公式清单对读者查询有用，即使不适合进入闭环主句，也必须进入 `## 结构化明细转交`；不得只在输入处置摘要中说“已归一”后让明细消失。
- Agent 必须按 S5 明细粒度三分法裁定转交方式：
  - **完整展开**：读者需要逐项查询或逐项判断；每行可能改变身份、资格、奖励、状态、字段含义、时间窗、可见文案或例外；行数有限且来源稳定。输出表格，保留关键列、行标识、来源名称和例外/备注。
  - **规则化压缩**：来源行高度同构，能由稳定公式、连续编号、等差阈值、固定命名模式或明确范围无损生成；单行没有独立例外含义。输出范围、生成规则、端点、步长、例外和至少 1-2 个示例，禁止只写“若干/多个/相关”。
  - **待确认**：来源冲突、不完整、只给设计稿占位、字段含义未闭环、是否用户可见未确认、展示位置或适用范围不稳定。不得伪完整展开；进入 `## 待裁决关键问题` 或 S6 `## 待确认事项`，写清待补材料与补齐后影响。
- Agent 必须识别半闭环：业务规则明确但实现/API/字段/检测方式未明确时，不得整体降级为待裁决，也不得整体升格为完整承诺。
- Agent 必须做语义归一：一条闭环链只能对应一个业务判定对象；页面、接口、字段、卡片、弹窗、列表只是证据位置、字段锚点或展示容器。同一业务动作在多个容器出现时，写成一条主规则，并在链内列“展示位置/字段锚点/证据来源”。
- Agent 必须做顺序归一：S1 同页顺序只代表来源陈列顺序，不能自动当作业务执行顺序。若来源顺序体现业务流程，S5 保留并说明；否则按 `准入/资格 -> 前置校验 -> 核心判定/计算 -> 结算/状态落账 -> 展示/运营 -> 占位补录` 重排。
- Agent 必须先写组织顺序计划再写闭环链；闭环链的 `### 链 N：标题` 必须与 `## 组织顺序说明` 中的链号、标题和顺序一致。
- Agent 必须保持全稿结构一致：领域概述和输入处置摘要按组织顺序概括；待裁决问题按关联链顺序排列，并在每个问题中写 `关联链：链 N` 或 `关联前置域：...`，且必须写 `决策影响`。
- Agent 必须保持互链一致：闭环链写 `关联待裁决：问题 N` 时，`问题 N` 必须存在，且问题块必须反向绑定该链；禁止链指向无关问题。
- Agent 必须保持领域边界降层：排除材料、噪声、工程协作、发布/合规支撑、待迁移主题、待归属材料不得写成 `领域对象`；只能写入输入处置摘要、待裁决前置域或排除说明。
- Agent 必须保持交付语境降层：体验版、bug list、sprint/retro、代码提交频率、三方协作、项目启动/完成日期和阶段验收日期不得进入 `## 已闭环决策链` 的核心规则；如影响用户可见质量，只能写成边界候选、待裁决问题或展示质量支撑证据。
- Agent 必须做模型分层：一等业务对象、指标/字段、展示容器、对象关系、状态机/状态转换、边界候选分开写；禁止把进度、公式、金额字段、API token、页面卡片写成一等业务对象。
- Agent 必须做模型-链一致挂载：闭环链的 `领域对象` 必须选自 `一等业务对象`；若规则实际围绕指标、公式、金额、字段、页面或卡片，必须挂到其所属一等业务对象，并把指标/字段/容器写入 `展示容器/字段锚点`。
- 待裁决问题若阻塞指标/字段定义，必须说明它归属的一等业务对象，不能只说阻塞某个字段或公式。
- Agent 必须先按 S4 领域模型判断源材料中的一等业务对象，不能让页面/API/字段反客为主。
- 闭环区禁止占位语句（如“待补充/按来源条件触发/按来源动作/待确认对象”）
- `未确定/待确认/TBD` 必须写入 `## 待裁决关键问题`，不得留在闭环区
- 同一规则簇只承载一个业务判定问题；禁止把不同判定问题混并到同一链
- 禁止把同一业务动作仅因出现在不同 UI 容器/API 字段中拆成多条链；若确需拆分，必须说明判定对象不同。
- S3 `propositions` 高贡献来源（同源高价值 contract/evidence 达阈值）必须在 S5 工作稿被显式引用
- 若 Agent 判断某来源语义不进入主链，必须能归入待裁决、`presentation_context`、实现支撑或噪声，并说明为什么不构成业务判定；不得无解释丢弃影响业务判定的材料。
- 若输入处置摘要声明某类材料进入闭环或待裁决，正文必须有对应闭环链或待裁决问题。
- S5 必须按 `distill-authoring-contract.md` 的 Markdown 骨架落稿：组织顺序标题不加粗、不加代码；每条闭环链显式写 `领域对象 / 状态变化 / 业务动作 / 展示容器/字段锚点`；结构化明细每个 `###` 必须是表格或分层列表；待裁决问题必须写 `关联链` 或 `关联前置域` 以及 `决策影响`。
- 脚本门禁：`python3 scripts/distill/s5_work_draft_quality.py --root-id <R>` 只验证 S5 工作稿显式契约，包括闭环链必填字段、组织顺序一致、待裁决互链、未决词位置、结构化明细形态；不得生成或替代 S5 语义正文。

S5 合并验收（防混淆）：

- 先按 `proposition_items` 的 `decision_block` / `semantic_roles` / `decision_track` 形成业务判定问题，再写规则链；同判定问题允许跨页合并证据，不再按单句拼接
- 同一规则簇只承载一个业务判定问题（可见性/资格/发放/状态迁移其一）
- 触发条件或时间窗不同的条文必须拆分，禁止“标题相似”就硬并
- 术语保持单义；若同词多义，先在术语小节定义后再写规则
- 跨页规则冲突必须落入“裁决/待定”，禁止在正文静默覆盖
- 接口/字段信息仅作为支撑材料，禁止反客为主覆盖业务主线

**落稿前通读**：`distill-quality-bar.md`（**§目标函数**、§落稿前分流、§禁止项）、`distill-authoring-contract.md`（**S5/S6 最小作者契约**）、`distill-document-skeleton.md`（**S4/S5**）、`strategy.md` 第二节。

### S6 · 定稿（Compose ④）

| 产出 | 规则 |
|------|------|
| `_deliver/<slug>/<slug>-领域知识定稿.md` | **读者向领域知识产品**；risk/split **默认只读此文件** |

S6 禁止：

- 模板句替代条件（例如“进入业务场景并满足前置条件时生效”）
- 模板句替代后果（例如“影响页面展示或流程分支，以实现为准”）
- 用“待后续实现确认”覆盖应当在本稿明确的规则条文
- 在 S6 引入 S4/S5 未出现的新业务语义（S6 仅允许读者向表达转换）
- 用模板拼接生成读者句（如重复“用户可见用户可见”、明显截断的“当...时”）
- 把 S5 的边界候选、噪声、工程协作或发布支撑材料升格为核心业务规则
- 把体验版、bug list、sprint/retro、代码提交频率、三方协作、项目日期或阶段验收节奏写入 `## 核心业务规则`；这类内容只能作为“不在本文展开”、待确认事项或溯源边界，除非 S5 已证明它直接改变用户可见业务承诺
- 用英文替代中文叙述；关键业务术语必须采用中文主名，首次出现用 `中文术语（English Term）` 保留来源原名；必要英文若不是来源链接/路径，必须作为字段/API/系统名锚点或在 `## 术语说明` 中解释
- 残留流程阶段语言、内部验收语境或旧黑话；通用禁用表达由 `domain-knowledge/language/s6-reader-language-policy.json` 配置，脚本只读取策略并报告命中类别，不写业务域规则
- 把来源中的映射表、状态枚举、字段清单、公式/阈值表、时间窗表或可见文案清单压缩成不可查询的摘要；这些明细若影响读者判断规则路径，必须保留为可查结构或进入待确认事项

S6 核心规则表达要求：

- 用读者向自然语言表达规则，不使用固定字段模板兜底。
- 每个核心规则小节必须是读者决策卡片，稳定包含 `已确认规则`、`待确认边界`、`用户可见影响`、`关联待确认事项`；每个标签必须作为独立粗体列表项，具体条件、分支、时间窗、例外、可见后果和来源语义放入缩进子项。这些是产品化阅读结构，不是旧规则簇字段模板。
- `已确认规则` 的一级 bullet 只承载一个读者判断点；不得用分号把多个分支、阶段、目标、奖励或展示后果压缩在同一条里。需要枚举时，先写总述，再用缩进子项或 `## 关键明细` 表达。
- 主文必须中文为主；凡在 `## 术语说明` 声明为 `中文术语（English Term）` 的关键业务术语，如果正文使用该中文术语，正文首次出现必须写作同样的 `中文术语（English Term）`，后续可只用中文。
- 必要英文只保留为括号内来源原名、字段/API/系统名、业务专有缩写或来源链接/路径。
- 字段/API/系统名必须用反引号作为锚点；业务专有缩写必须在 `## 术语说明` 解释。
- 每条核心规则必须能追溯到 S5 闭环链或待裁决问题。
- 每条核心规则必须保留 S5 支撑的条件、分支、时间窗、例外、用户可见影响和来源语义。
- 指标、字段、展示容器只作为解释规则的锚点，不反客为主。
- 当规则依赖结构化明细时，读者决策卡片只写决策含义；可查明细放入 `## 关键明细`，或在同一卡片下使用 `明细` 子块。不要用“详见来源”替代明细，也不要把明细散落到长句里。
- S6 必须按 `distill-authoring-contract.md` 的 Markdown 骨架落稿：领域模型摘要使用分层标签；每张决策卡片使用独立粗体标签和缩进子项；`## 关键明细` 的每个 `###` 必须是表格或分层列表；`## 待确认事项` 的每条行动项必须以 `影响规则` 为主项，并缩进写 `待确认/待补充`、`建议确认人`、`确认后影响`。

S6 章节强制结构：

- `## 概述与范围`：说明本主题覆盖对象、业务范围、对外读者视角
- `## 不在本文展开`：列出工程实现、噪声、边界候选或待迁移主题
- `## 不在本文展开`：必须承接交付/协作/验收节奏类材料的降层说明，不得让这类内容漂移到核心规则
- `## 领域模型摘要`：只承接 S5 的一等业务对象、对象关系、状态机，不重新建模；一等业务对象、对象关系、状态机/状态转换必须用粗体标签加缩进子项表达，避免把多个对象或状态压成一个长列表项
- `## 核心业务规则`：按 S5 组织顺序写读者决策卡片；每卡必须用独立粗体标签区分已确认规则、待确认边界、用户可见影响、关联待确认事项，并把具体内容写入缩进子项
- `## 关键明细`（条件性）：当 S1/S5 有映射表、状态枚举、字段清单、公式/阈值表、时间窗表或可见文案清单时必须出现；按业务规则分 `###` 小节，每个小节用表格或缩进列表保留可查询明细。若来源无法形成稳定明细，必须在 `## 待确认事项` 写明缺什么和补齐后影响。
- `## 术语说明`：只解释 S5/S6 已用术语，不新增规则；关键业务术语采用 `中文术语（English Term）`，并作为正文首次锚点检查的术语清单；凡 S6 主文保留的业务英文缩写或专有英文名必须在此解释
- `## 待确认事项`：按 `领域边界 / 规则冲突 / 数据与接口 / 政策与展示 / 待补充材料` 分类；每条待确认事项必须写成行动项，以 `影响规则` 作为主列表项，并在缩进子项中包含 `待确认/待补充`、`建议确认人`、`确认后影响`
- `## 溯源`：列工作稿、聚合索引、命题清单、命题 JSON 与物化目录
- 若存在占位簇：必须在 `## 待确认事项` 的 `待补充材料` 分类中出现

S6 生产方式（第一性，不是模板填空）：

- 先承接 **S5 分层模型摘要**：一等业务对象、对象关系、状态机只做表达转换
- 再写 **业务读者可读的规则链**：每条规则保留条件、分支、时间窗、例外、用户可见影响
- 再做 **结构化明细保真**：凡来源已有可查的表、枚举、字段映射、阈值或时间窗，不在规则卡片里压缩掉；保留为读者可检索的 `## 关键明细`
- 再做 **待定问题索引**：领域边界、规则冲突、数据与接口、政策与展示、待补充材料；每条待确认事项必须可行动
- 最后写 **溯源**：禁止工程噪声进入核心业务规则主线
- **人工判断强制点**：阈值规则冲突、时间窗冲突、状态迁移冲突，必须人工确认后才能出定稿

基于 **S5 工作稿**；可参考上一轮 [`glossary.md`](../../../domain-knowledge/language/glossary.md) 统一读者语言。本轮新增术语在 S6 后再沉淀回术语表。

S6 生成原则（主链路）：

- S6 是 S5 的读者向知识产品化表达转换层，不是语义再创造层。
- S6 可优化可读性与术语一致性，但不得新增/删除业务判定语义。
- 语义修订必须回到 S4/S5 完成，S6 只承接已确认语义。

**成稿完成（单主题）**：S7 目标语言定稿存在，且无证据不足横幅（或明确按非 SSOT 承认）；并跑通：

```bash
python3 scripts/distill/tagging_acceptance.py --root-id <R> --after-s7 --strict
```

**全库门禁**：`domain_check.py distill`（**S7 后**）。

---

## 用户话术

| 意图 | 说法 |
|------|------|
| 同步 + 认域 | `@generate-knowledge-from-wiki <url>`（默认到 **S2** 后停） |
| 跑成稿 | **`继续`** 或 `@distill-domain-knowledge <R>` |
| 某主题子步 | `… 主题 checkout S3` / `S4` / `S5` |

---

## 汇报模板

- **Ingest（S1）**：页数、落盘根
- **Recognize / 备料（S2）**：领域块；closure；确认页 **已确认 / 待确认** 行数
- **Compose / 成稿（S3–S6）**：各 **`确认`** 主题：聚合 / 领域模型 / 工作稿 / 定稿 **有/无**
- **禁止**仅有 S3/S4/S5 却报「中文定稿完成」

---

## 附录 · 步骤速查

### 三阶段 ↔ S1–S6

| 阶段 | 步 | 目标 | 人工 |
|------|-----|------|------|
| **Ingest** | **S1** | Confluence → `materialized/`（机器粗分） | 无 |
| **Recognize** | **S2** | 确认页 + closure（命题级） | **停**：标 **`确认`** |
| **Compose** | **S3** | `_aggregate/`（仅确认行） | 无 |
| **Compose** | **S4 / S5 / S6** | 领域模型 → 工作稿 → 中文定稿 | 可选验收 |

### 备料 / 成稿（别名）

| 段 | 步 | 目标 | 人工 |
|----|-----|------|------|
| **备料** | **S1 + S2** | Ingest + Recognize | **停**：标 **`确认`** |
| **成稿** | **S3 → S6** | Compose | 无（或可选验收） |

### 步 ↔ 文档与门禁

| 步 | Agent 必读 | 主要写入 | 门禁 |
|----|------------|----------|------|
| S1 | `SKILL` → `S1-SYNC-CLI.md` | `extracted/`、`materialized/`、`PIPELINE_HANDOFF.json` | 脚本退出码 |
| S2 | 本 RUNBOOK · `strategy.md` §2 | `DOMAIN_MODULE_CHECKLIST.md`、`_materialization_closure.json`、`S2_DECISION_LEDGER.json`、`S2_REVIEW_DECISIONS.json` | `python3 scripts/distill/coverage.py --root-id <R>` |
| S3 | 本 RUNBOOK | `_aggregate/<slug>/` | coverage（建议） |
| S3.5 | 本 RUNBOOK | `_aggregate/<slug>/*-propositions.json`、`*-命题清单.md` | `python3 scripts/distill/proposition_quality.py --root-id <R>` |
| S3.6 | 本 RUNBOOK | `_aggregate/<slug>/*-decision-atoms.json|md`、`*-conflict-ledger.md` | `python3 scripts/distill/decision_atom_quality.py --root-id <R>` + `python3 scripts/distill/conflict_ledger_quality.py --root-id <R>` |
| S4 | `distill-quality-bar.md` §目标函数 · `distill-document-skeleton.md` | `_deliver/*-工作稿.md`（Agent 产文） | `quality.py`（按 Skill MUST 验证） + `domain_layout.py` |
| S6 | 上一轮 `glossary.md`（可选参考）+ 本轮术语备注 | `_deliver/*-定稿.md`（Agent 产文）；S6 后自动更新 `glossary.md` | `python3 scripts/run_distill_gate.py --root-id <R>`（含 `domain_check distill` + `glossary_update.py`） |

**语言**：S1–S5 = 源语言；**仅 S6** = 简体中文。

### 门禁分层与失败归属（S2/S3/S4/S5/S6）

| 层 | 代表门禁 | 失败主归属 | 处理原则 |
|---|---|---|---|
| S2 认域层 | `coverage.py` | Script 执行层（识别/closure/阻断） | 先修识别与映射规则，再进 S3 |
| S3 结构层 | `proposition_quality.py`、`s3_quality.py`、`decision_atom_quality.py`、`conflict_ledger_quality.py` | Script 执行层（抽取/归一/索引） | 先修抽取与标准化，不在 S4/S5/S6 打补丁 |
| S4 模型层 | 工作稿 `## 领域模型` 验收 | Skill/Agent 契约层（领域对象与状态建模） | 回到领域模型，不用规则链堆叠掩盖模型缺失 |
| S5 语义层 | 工作稿人工验收（模型挂载、规则链密度、冲突显式化） | Skill/Agent 契约层（重挂载与裁决） | 回到语义重挂载，不改门禁阈值掩盖问题 |
| S6 承诺层 | `s6_reader_quality.py` | 混合归属：边界越界归 Skill，读者结构缺失归 Script | S6 做读者向表达转换；语义缺陷回退到 S4/S5 修复 |

快速判责：
- **结构缺失/字段缺失/索引断裂**：优先判为 Script 层问题。
- **冲突未裁决/规则混并/承诺越界**：优先判为 Skill/Agent 层问题。
- **意图分流误判**：先在 Script 层收敛触发条件（高置信触发），禁止通过放宽总门槛掩盖。

### 补跑

| 场景 | 入口 |
|------|------|
| 不跑同步 | [`distill-domain-knowledge`](../distill-domain-knowledge/SKILL.md) |
| 标完 **`确认`** | **`继续`**（S3→S6） |

分阶段重跑（脚本）：
- `python3 scripts/distill/compose_rerun.py --root-id <R> --stage s3_build`
- `python3 scripts/distill/compose_rerun.py --root-id <R> --stage s4_work_draft`（仅校验 `_deliver/*-工作稿.md` 已存在且不旧于 S3）
- `python3 scripts/distill/compose_rerun.py --root-id <R> --stage s6_final_draft`（仅校验 `_deliver/*-定稿.md` 已存在）

## Next

`@requirement-risk` → `@ticket-splitter`（证据：`_deliver/…定稿.md`）。
