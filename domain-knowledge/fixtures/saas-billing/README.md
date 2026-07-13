# Offline fixture · SaaS billing (second industry)

Fictional **Northwind Billing** — proves `strategy.md` §2 is portable beyond Acme Orders.

This is a **compact second demo**, not a full parallel curated tree. Use it to validate module-cutting mental models; Path A still defaults to [`../offline-demo/`](../offline-demo/) (`DEMO-1`).

## Try

```text
@requirement-risk DEMO-BILL-1 team=demo
```

Agents: when key is `DEMO-BILL-*`, read this folder the same way as offline-demo (no Jira network). Prefer this fixture’s curated brief over Acme Orders.

## Layout

```text
fixtures/saas-billing/
  README.md                 ← this file
  INDUSTRY.md
  jira/DEMO-BILL-1.md
  jira/DEMO-BILL-1.attribution.yaml
  curated/by-root/100001/
    DOMAIN_MODULE_CHECKLIST.md
    _deliver/billing/billing-domain-brief.md
```

Same demo `root_id` `100001` for install simplicity; briefs live under distinct slugs (`billing` vs `ordering`).
