> English SSOT: [`domain-module-checklist.mdc`](./domain-module-checklist.mdc).

# 领域模块确认页（DOMAIN_MODULE_CHECKLIST.md）

**何时适用**：编辑或刷新 `domain-knowledge/curated/by-root/<根>/DOMAIN_MODULE_CHECKLIST.md`；或刚完成 **`@generate-knowledge-from-wiki`** / **`@distill-domain-knowledge`**。

**版式**：`domain-knowledge/DOMAIN_MODULE_CHECKLIST.template.md` · **全流程**：`.cursor/skills/generate-knowledge-from-wiki/RUNBOOK.md`

**窄屏版式（必守）**：每个主题一块 `### 主题名` + `- **字段**: 值`；**禁止**再写「主题 | strategy | … | 状态」宽表。人通常只改 **状态**（`待确认` → `确认`）。状态文案见 `domain-knowledge/language/deliverable-locale-tokens.json`。

## 1. 标尺

只使用 `domain-knowledge/strategy.md` **第二节**——**不**另创行业标准。

## 2. S2（刷新本页时）

- **主题块** = `strategy.md` 第二节 × 扫描 `materialized/`
- **打标** = 每个 `materialized/**/*.md` → `_materialization_closure.json`
- **禁止**：在多个产出目录重复粘贴同一段 `materialized/` 原文
- **分散素材防漏**：还须对 `materialized/` 做全文检索与语义补漏；上一轮稳定 `glossary.md` 仅作同义词/缩写提示，不得作为领域边界依据。补全路径写入 closure 与确认页，本轮新术语写入 **术语备注**；**不得**仅凭文件名或 `facet-*` 认定已覆盖
- **暂停**：等人根据打标验收（`tagging_acceptance.py`）将有来源的模块标为 **`确认`**；零来源保持 **待确认**；禁止引导「全部确认」
- **保持业态裁决轴**：产品面页重挂载入现有 slug（[`industry-axis-remount.md`](../skills/generate-knowledge-from-wiki/references/industry-axis-remount.md)）；默认不重建 Mall/惠/Gateway 模块
- 刷新时 S2 按状态 + 来源数重写 **备注**（确认后清除过时的「等待人工确认」）

## 3. 成稿（用户 **`继续`**）

仅 **`确认`** 模块：**S3** `_aggregate/` → **S4** 领域模型 → **S5** 工作稿 → **S6** 原语言定稿 → **S7** 目标语言定稿 — 重挂载证据必须写进规则卡或待确认。

## 4. 门禁

- S2 后（确认前必做）：`python3 scripts/distill/tagging_acceptance.py --root-id <根>`
- S2 后（建议）：`python3 scripts/distill/coverage.py --root-id <根>`
- S3 后：`python3 scripts/distill/tagging_acceptance.py --root-id <根> --after-s3`
- S7 后：`python3 scripts/distill/tagging_acceptance.py --root-id <根> --after-s7 --strict`，再 `python3 scripts/domain_check.py distill --root-id <根>`
- 已确认 + 有来源 + S7 零 `### 规则` = 假覆盖 → 改回 **待确认**

## 5. 本页附录链接

`_materialization_closure.json`、`_附录/`（若存在）。

## 6. 禁止

- 编造 Confluence 未出现的业务数字或政策；不确定写「待定」并保留溯源
- **S1–S5** 禁止翻译
- `materialized/` 仅在定稿 **`## 溯源`** 中单行引用（见 `distill-quality-bar.md`）
- 把确认页改回宽 Markdown 表
