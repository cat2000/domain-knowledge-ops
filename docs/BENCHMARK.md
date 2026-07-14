# Benchmark · story review with vs without an S7 brief

Same ticket: offline **`DEMO-1`** (Acme Orders amend open order).

This is the **Path B aha** in [`WALKTHROUGH.md`](../WALKTHROUGH.md) — also useful for launch posts. Qualitative, not a CI metric.

## Without a domain brief

Typical agent behavior when only the Jira body is available:

| Observation | Why it hurts delivery |
|-------------|------------------------|
| Treats all AC as equally firm | Misses that approval-on-increase is still open in comments |
| Invents API / WMS scope | Out-of-scope lines in the ticket get re-expanded |
| Weak quote-expiry framing | “Save disabled” becomes a vague UX note, not a business gate |
| No shared vocabulary | “Open” vs fulfillment states stay ambiguous across stories |

## With the shipped S7 brief

Using [`ordering-domain-brief.md`](../domain-knowledge/fixtures/offline-demo/curated/by-root/100001/_deliver/ordering/ordering-domain-brief.md):

| Observation | Evidence in sample output |
|-------------|---------------------------|
| MUST items cite quote validity + Open status | [`docs/demo/requirement-risk-DEMO-1.sample.md`](demo/requirement-risk-DEMO-1.sample.md) |
| Open questions stay **should clarify**, not false MUST | Quantity-up approval / Partially Shipped |
| INVEST slices align User/System/Contract faces to brief rules | [`docs/demo/ticket-splitter-DEMO-1.sample.md`](demo/ticket-splitter-DEMO-1.sample.md) |
| Out-of-scope stays out | No WMS / price renegotiation slices |

## How to re-run locally

**With brief (Path A):**

```text
@requirement-risk DEMO-1 team=demo
@ticket-splitter DEMO-1 team=demo
```

**Without brief (Path B):**

```text
@requirement-risk DEMO-1 team=demo
Path B: use only the Jira/fixture ticket body. Do not read domain briefs, curated/, or fixtures under _deliver/.
```

Compare the two reports using the tables above. Also compare Path A output to `docs/demo/*.sample.md`. Drift in wording is fine; **rule anchors** (Open + valid quote, expired quote blocks save, shipped lines read-only) should appear in the with-brief pass.

## Portability check (Path B2)

Repeat with `@requirement-risk DEMO-BILL-1 team=demo` and [`saas-billing`](../domain-knowledge/fixtures/saas-billing/) — same skill path, different industry brief.
