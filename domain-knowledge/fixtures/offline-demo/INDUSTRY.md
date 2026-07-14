# Acme Orders · industry map (offline fixture)

> Companion to [`WALKTHROUGH.md`](../../../WALKTHROUGH.md) Path B.  
> Fictional B2B ordering portal — **not** a shipped production profile.

## Strategy → modules (from `strategy.example.md` §2.3)

| Business module (example) | Slug (example) | Axis |
|---------------------------|----------------|------|
| Place / amend order | `ordering` | Who may submit/change an order under which quote version |
| Fulfillment visibility | `fulfillment-visibility` | Which stages/ETA the buyer sees |
| Identity & access | `identity-access` | Who can see price / place orders |
| Notifications | `notifications` | Who is notified on status change |

This fixture **ships only** the `ordering` brief — enough for `DEMO-1`. The other rows are format examples only.

## Ticket → brief

| Artifact | Role |
|----------|------|
| `jira/DEMO-1.md` | Story: amend line qty on **Open** order while quote valid |
| `jira/DEMO-1.attribution.yaml` | Points evidence at `ordering` |
| `_deliver/ordering/ordering-domain-brief.md` | Adjudicated rules (quote version, amend eligibility, partial ship) |

## What Path B proves

Same ticket, **with vs without** a reader brief — see [`docs/BENCHMARK.md`](../../../docs/BENCHMARK.md).

Loop: **module cut → brief → grounded review**. Path C builds your brief after `@setup-domain-ops`.
