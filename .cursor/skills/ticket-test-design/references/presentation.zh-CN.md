# ticket-test-design · 呈现合同（中文读者）

> 与 [`.cursor/rules/ticket_test_design.md`](../../../rules/ticket_test_design.md) **叠加**：实质字段以英文 rule 为准；可读性以本节为准。  
> 英文呈现：[`presentation.md`](./presentation.md)。

## 要点

先给**摘要**（能否测、必测几条），再给**验收合同**，再给用例。用例正文用**缩进字段**（类 YAML），不用宽表，不用 emoji 强制格式。

每条 `(given)` 验收标准须有 **必测** `proves`，或写 **Must-deferred** 并降低 **合同就绪**。摘要须拆开 **合同就绪** 与 **应测包**（勿再用「可凭必测+应测上线」单行）。非 AC 蕴含用 `supplements:`；must/should 标 `automate: candidate|manual`（不为自动化写框架细节）。

## 读者向标题

| 英文骨架标题 | 中文读者标题 |
|--------------|--------------|
| Summary | 摘要 |
| Acceptance | 验收标准 |
| Design | 设计选型 |
| Scope | 范围 |
| Must | 必测 |
| Should | 应测 |
| Later | 以后 |
| Environment | 环境 |

用例标题仍用：`### TC-001 · must · <一句话>`（`must`/`should` 英文键保留，便于门禁）。

缩进键名保持英文：`proves` / `given` / `when` / `then` / `data_deps` 等。

## 摘要示例

```markdown
## 摘要

- **范围**：…
- **合同就绪**：contract-ready | blocked-by-ac-gaps | blocked-by-must-deferred | blocked-by-evidence
- **应测包**：建议跑应测 N 条；可含弱 oracle — 不挡合同 Done | 无应测
- **计数**：必测 N · 应测 N · 以后 N
- **残余风险**：…
```
