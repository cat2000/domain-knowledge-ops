> English SSOT: [`strategy.example.md`](./strategy.example.md).

# strategy.example.md — 虚构业态填写示例

> **仅作格式参考。** 不要把下列模块复制进你们的默认 `s2-domain-profiles.json`。  
> 真实团队应编辑 [`strategy.md`](strategy.md) 第二节，再由 Cursor 派生 profiles。

下文模拟一家 **B2B 订购平台**「Acme Orders」的填法。

---

## 二、组织与行业上下文（示例已填）

### 2.1 组织与边界

- **组织 / 产品线名称**：Acme Orders（北美订购门户）
- **权威 Confluence 根**：`team-roots.json` → team `orders`，root_id `200001`
- **团队 key**：`orders`
- **产品边界一句话**：买方下单、改单、履约可见状态在域内；仓储 WMS 内部算法在域外。

### 2.2 业态与主体

- **业态类型**：B2B 订购与履约状态
- **规则主要适用于谁**：买方采购员、卖方客服、内部履约协调员
- **市场或监管语境**：无特定金融监管；合同价以报价单版本为准
- **版本 / 政策年度是否影响规则**：报价单 `quote_version` 影响可下单价

### 2.3 规则密集区（候选领域模块）

| 候选主题（业务名） | 一句话轴心（判定什么） | 典型素材关键词（可选） |
|--------------------|------------------------|------------------------|
| 下单与改单 | 谁在什么报价版本下可提交/修改订单 | order, cart, amend, quote |
| 履约可见状态 | 买家看到哪些履约阶段与 ETA | fulfillment, ship, ETA, status |
| 身份与权限 | 采购员角色能否看价/下单 | role, permission, buyer, SSO |
| 通知与触达 | 状态变更时谁收到何种通知 | email, webhook, notify |

对应派生后的 slug 示例（**仅示例**）：`ordering`、`fulfillment-visibility`、`identity-access`、`notifications`。

### 2.4 典型判定问题

1. 采购员在报价过期后是否仍可按下单按钮，看到什么提示？
2. 部分发货时买家门户展示「进行中」还是按行项目拆分状态？
3. 只读观察员角色能否看到合同价？

### 2.5 时间与周期

- 报价有效期、承诺发货窗口、取消截止时间（以合同条款页为准）

### 2.6 强化 / 弱化

| 强化 | 弱化 |
|------|------|
| 报价版本、可下单条件、门户可见状态 | WMS 拣货路径、内部 Slack 值班表 |

### 2.7 政策 vs 实现

- **规范层**：商业条款 / 报价政策 Confluence 页
- **实现层**：Orders API 字段表进溯源，不进规则主线

---

## 派生提示（给 Agent）

根据上表生成 `checklist_themes` 四条、`facet-ordering` 等 `s1_facets`、以及 `s2.domain_cues`；`module_seeds` 的 `teams` 填 `["orders"]`。人确认后再同步 Wiki。
