> English SSOT: [`DOMAIN_MODULE_CHECKLIST.template.md`](./DOMAIN_MODULE_CHECKLIST.template.md).

# 领域模块确认页 · 根 `<ROOT_PAGE_ID>`

复制到：`domain-knowledge/curated/by-root/<ROOT_PAGE_ID>/DOMAIN_MODULE_CHECKLIST.md`，将占位符替换为实际根 ID 与路径。

**本页用途**：团队 **确认领域块划分**；模块 **状态** = `确认` 授权 Agent 跑 **成稿**（S3 → S7）。**`确认` ≠ 目标语言定稿已完成**。

**版式（窄屏友好）**：每个主题一块 `###` + 字段列表；人通常只需改 **状态** 一行。不要再写宽表。

## 生命周期（与 Cursor 分工）

**主题从哪来**：

- **每次重扫**，Cursor 根据 **两份输入** 刷新模块块：
  1. **行业领域标尺**：[`strategy.md`](strategy.md) **第二节**；
  2. **扫描事实**：当前根下 **`materialized/`** 里已识别的子目录与代表 `.md`。
- **人**可 **增删改块、改状态/备注/术语备注**；重扫时 Cursor **合并**：更新扫描路径，**默认保留** **`确认`**（禁止无故降级为 `初稿` / `待确认`）。

**首次 / 重扫**：

- **首次**：若无该文件，由 **`@generate-knowledge-from-wiki` / `distill-domain-knowledge`** 创建草案。
- **重扫**：**增量合并**——刷新路径；与人手字段冲突时 **以人的状态/备注为准**（除非用户明确要求重置）。

**标尺**：[`strategy.md`](strategy.md) **第二节**。

## 谁维护、何时更新

- 每次 **`@generate-knowledge-from-wiki` 重扫** → **Cursor**：S2 刷新本页 + `_materialization_closure.json`
- 认域后 → **人**：将认可模块的 **状态** 标为 **`确认`**
- **`继续` 后** → **Cursor**：对 **`确认`** 模块跑 S3 → S7

## 流水线结构（与 RUNBOOK 一致）

- **S2**：刷新本页；全文件打标 → `_materialization_closure.json`（不改写正文语言）
- **S3**：仅 `确认` 模块 → `_aggregate/<slug>/`
- **S4 / S5**：领域模型 + 工作稿 → `_deliver/…-工作稿.md`
- **S6**：原语言裁决定稿 → `…-source-brief.md`
- **S7**：目标语言定稿 → `…-领域知识定稿.md` / `…-domain-brief.md`（`deliverable_locale`）

**未标 `确认` 不做 S3–S7**。

## 必读主题（短清单）

「状态」含 **`确认`**（仅此触发 **成稿**）。

### （Cursor：按 strategy 第二节 × 扫描起块）

- **命题 slug**: `example-slug`
- **strategy 维度**: （轴心一句话）
- **领域子目录（扫描）**: `facet-example/`
- **主入口**: `_deliver/example-slug/example-slug-领域知识-工作稿.md`
- **状态**: 待确认
- **术语备注**:
- **备注**:

## 溯源与附录

- 闭环 JSON：`_materialization_closure.json`
- 非领域附录：如 `_附录/非领域/`

## 门禁脚本

- S2 后建议：`python3 scripts/distill/coverage.py --root-id <ID>`
- S7 后全量：`python3 scripts/domain_check.py distill --root-id <ID>`

## 增量主题

（需要时在下方追加同结构的 `###` 模块块。）
