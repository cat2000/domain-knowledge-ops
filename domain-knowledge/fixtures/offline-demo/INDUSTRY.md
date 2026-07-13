# Acme Orders · industry map (offline fixture)

> Zero-config companion to [`WALKTHROUGH.md`](../../../WALKTHROUGH.md) Path B.  
> Fictional B2B ordering portal — **not** a shipped production profile.

## Strategy → modules (from `strategy.example.md`)

| Business module (example) | Slug (example) | Axis |
|---------------------------|----------------|------|
| Place / amend order | `ordering` | Who may submit/change an order under which quote version |
| Fulfillment visibility | `fulfillment-visibility` | Which stages/ETA the buyer sees |
| Identity & access | `identity-access` | Who can see price / place orders |
| Notifications | `notifications` | Who is notified on status change |

This fixture **ships only** the `ordering` brief — enough for `DEMO-1`.

## Ticket → brief

| Artifact | Role |
|----------|------|
| `jira/DEMO-1.md` | Story: amend line qty on **Open** order while quote valid |
| `jira/DEMO-1.attribution.yaml` | Points evidence at `ordering` |
| `_deliver/ordering/ordering-domain-brief.md` | Adjudicated rules (quote version, amend eligibility, partial ship) — English SSOT, with `ordering-领域知识定稿.md` as zh-CN sibling |

## What Path B proves

Without Confluence you can still see the product loop:

**industry cut (strategy §2) → module brief → story risk / INVEST split**

When you run Path C, `@setup-domain-ops` fills **your** §2 the same way `strategy.example.md` demonstrates — then wiki sync materializes **your** modules, not Acme’s.
