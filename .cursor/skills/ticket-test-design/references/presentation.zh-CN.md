# ticket-test-design · 呈现合同（中文读者）

> 与 [`.cursor/rules/ticket_test_design.md`](../../../rules/ticket_test_design.md) **叠加**：实质字段以英文 rule 为准；可读性以本节为准。  
> 英文呈现：[`presentation.md`](./presentation.md)。

## 要点

优化目标是 **约 60 秒能开测**，不是写证据备忘录。

顺序：**摘要（决策板）→ 验收标准 → 必测 → 应测 → 以后 →（可选）设计选型 / 环境**。  
用例正文用缩进字段；**禁止**用表格压缩掉 `given/when/then`（聊天交付须与 draft 文件一致）。

## 摘要预算

必给且短（每行一句）：

- **范围**
- **合同就绪**
- **应测包**
- **计数**

可选各一行：残余风险、Evidence（路径指针即可）。勿在摘要解释「为何没有 formal AC」。

## 验收 / 必测句式

AC 与 `given/when/then` 用 **在哪 + 做什么 + 看到什么**；产品背景、路由歧义、分支名争论 → 一条短 `notes` 或「以后」，不要写进 `when`。

读者散文用中文；门禁键保持英文：`must` / `proves` / `given` / `when` / `then` / `automate` / `Must-deferred`。

## 应测优先（实质见英文 rule）

必测须**可判定**（结果 + oracle + seed）；残余须**闭合**；数据/合同类 AC 优先 `level: api|logic`。`needed` 扫描须有处置。环境写清 build + seed。本 skill 不做发布回归包 / 度量体系 / 默认 NFR 平台。

## 必测字段默认集

默认只写：`proves` · `automate` · `given` · `when` · `then`。  
`technique` / `level` / `kind` / `data_deps` / 长 `notes` 仅当影响怎么跑时再加。

## 读者向标题

| 英文骨架 | 中文读者 |
|----------|----------|
| Summary | 摘要 |
| Acceptance | 验收标准 |
| Scope | 范围 |
| Must | 必测 |
| Should | 应测 |
| Later | 以后 |
| Design | 设计选型（建议放文末） |
| Environment | 环境 |

## 摘要示例

```markdown
## 摘要

- **范围**：Open 且报价有效时可改未发货行数量；不含改价/加 SKU/WMS
- **合同就绪**：contract-ready
- **应测包**：应测 1（弱 API 角色）— 不挡合同 Done
- **计数**：必测 6 · 应测 1 · 以后 2
- **残余风险**：加量是否需卖方审批未决
- **Evidence**：offline-fixture · ordering S7
```
