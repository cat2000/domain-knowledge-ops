# add-knowledge-from-jira · Classify CLI（参数 / 排障）

> English SSOT: [`CLASSIFY-CLI.md`](./CLASSIFY-CLI.md).
>
> **阶段**：**Classify**（Jira 四阶段之 ②）  
> **执行剧本**：[`RUNBOOK.md`](./RUNBOOK.md) · **用户入口**：[`SKILL.md`](./SKILL.md) · **脚本备料编排**：`scripts/run_jira_knowledge.py`（无 flag = Ingest + Classify + 门禁）  
> **前置**：[`INGEST-CLI.md`](./INGEST-CLI.md)（`jira/raw/` 须已存在）

**Classify ≠ Recognize**：本阶段是 **票级分诊**（`attribution/`、主题 **索引**）；命题级认域 + 人 **`确认`** 在 **Recognize**（Wiki RUNBOOK · S2）。

---

## 编排 vs 单步

| 方式 | 命令 | 何时用 |
|------|------|--------|
| **推荐 · 脚本备料** | `python3 scripts/run_jira_knowledge.py --team <t>` | 默认：从最早 Sprint 拉到当前 Sprint（含当前）+ Classify + `--full-raw` 门禁 → **停** |
| **仅 Classify** | 先确保 `raw/` 已有，再跑下面两步 | Ingest 已单独跑完、只补归因/索引 |
| **跳过 Classify** | `run_jira_knowledge.py --skip-attribute` | 维护者调试；**勿**当常态备料 |

`run_jira_knowledge.py` 内部顺序（Classify 段）：

1. `jira/steps/attribute.py`
2. `jira/steps/read_business.py`
3. `domain_check.py jira --team <t> --full-raw`

---

## ① attribute · 票级归属

```bash
python3 scripts/jira/steps/attribute.py --team cma
python3 scripts/jira/steps/attribute.py --team cma --keys DEV-94211,DEV-94212
python3 scripts/jira/steps/attribute.py --team cma --no-preserve-cursor-reviewed
```

| 参数 | 含义 |
|------|------|
| `--team` | `bc` \| `wc` \| `cma`（必填） |
| `--keys` | 逗号分隔 KEY；省略则处理 `raw/*.json` 全量 |
| `--no-preserve-cursor-reviewed` | 覆盖已有 `cursor_review` / 高置信 YAML（**慎用**） |

**产出**：

- `jira/attribution/<KEY>.yaml`
- `jira/_ticket_attribution.json`
- 可选 `jira/_parent_index.json`（Ingest 带 parent 时）

**字段语义**：[`first-principles-attribution.md`](../../../domain-knowledge/jira/first-principles-attribution.md) · 团队规则 `domain-knowledge/jira/teams/<team>.json`

**Cursor B1**：复核 `attribution_method: cursor_review`、低置信票；WC 强制队列见 [`teams/wc-attribution.md`](../../../domain-knowledge/jira/teams/wc-attribution.md)。

---

## ② read_business · 主题索引（非摘录）

```bash
python3 scripts/jira/steps/read_business.py --team cma
python3 scripts/jira/steps/read_business.py --team cma --theme checkout
python3 scripts/jira/steps/read_business.py --team cma --confirmed-only
```

| 参数 | 含义 |
|------|------|
| `--team` | 默认 `cma` |
| `--theme` | 单主题 slug |
| `--confirmed-only` | 仅 checklist **`确认`** slug（**成稿前**刷新索引；非备料默认） |

**主题列表来源**（无 `--theme` 时）：

| 模式 | 何时 | 主题从哪来 |
|------|------|------------|
| **默认（备料）** | Classify / `run_jira_knowledge.py` | `_ticket_attribution.json` 中出现的 slug（∩ checklist allowed） |
| **`--confirmed-only`** | 人标 **`确认`** 后 | 仅 **`确认`** 行（与统一 Compose 准入同口径） |

**无 hardcoded fallback**。本批 attribution 未覆盖的主题 **不会** 写出 `遗漏扫描.md`。

**产出**（每主题）：

- `jira/by-theme/<theme>/遗漏扫描.md`（**索引**；Classify 层）
- 脚本日志 `read_text_total=` 为通读票计数

**禁止**：用 `遗漏扫描.md` 存在汇报 Jira 业务细则已并入或全管线完成。

---

## Classify 门禁

```bash
python3 scripts/domain_check.py jira --team cma --full-raw
```

脚本备料末 **必须** 通过后再接 **Recognize**（Cursor）。

| 后续门禁 | 阶段 | 命令 |
|----------|------|------|
| 备料就绪 | Classify | `domain_check jira --team <t> --full-raw` |
| 定稿质量 | Compose | `domain_check distill --root-id <R>` |

---

## 命令速查

```bash
# 脚本备料（Ingest + Classify + 门禁）
python3 scripts/run_jira_knowledge.py --team cma

# 仅 Classify（raw 已有）
python3 scripts/jira/steps/attribute.py --team cma
python3 scripts/jira/steps/read_business.py --team cma
python3 scripts/domain_check.py jira --team cma --full-raw

# 人标 确认 后 · 刷新已确认主题索引
python3 scripts/jira/steps/read_business.py --team cma --confirmed-only

# 单票重跑归属
python3 scripts/jira/steps/attribute.py --team cma --keys DEV-94211
python3 scripts/jira/steps/read_business.py --team cma --theme checkout
```

---

## 故障排查

| 现象 | 处理 |
|------|------|
| `missing attribution/…`（domain_check） | 先跑 `attribute.py` |
| `_ticket_attribution.json` 不存在 | 先跑 `attribute.py` |
| `read_business` 报错读 index | 同上；须 **attribute 先于 read_business** |
| `skip unknown theme` | slug 不在 checklist / 团队词表；查 `first-principles-attribution.md` |
| 票很多但 `business_extract: false` 居多 | 正常；索引队列 ≠ S3 业务证据准入队列（见 `pipeline-design.md`） |
| WC 大量 `cursor_review` | 跑 B1，见 `teams/wc-attribution.md` |

---

## 产物路径

```text
domain-knowledge/curated/by-root/<root_id>/jira/
  attribution/<KEY>.yaml
  _ticket_attribution.json
  by-theme/<theme>/
    遗漏扫描.md          # Classify · 索引（非 Jira业务规则摘录.md）
```

**不写**：`DOMAIN_MODULE_CHECKLIST.md`、`_deliver/`（Recognize / Compose 段）。
