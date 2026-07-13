# Industry map · Northwind Billing

| Strategy §2 axis (example) | Module slug | Shipped? |
|----------------------------|-------------|----------|
| Subscription entitlement → invoice state → buyer-visible charge | `billing` | Yes (this fixture) |
| Seat change / proration | `seats` | Checklist only (pending) |
| Dunning / payment retry | `collections` | Not cut |

## Story → brief

| File | Role |
|------|------|
| `jira/DEMO-BILL-1.md` | Story: change seat count mid-cycle with proration visibility |
| `jira/DEMO-BILL-1.attribution.yaml` | Points at `billing` |
| `_deliver/billing/billing-domain-brief.md` | S7 brief used by risk/split |

Compare with Acme Orders: [`../offline-demo/INDUSTRY.md`](../offline-demo/INDUSTRY.md).
