# Walkthrough — zero credentials to first value

Three paths. **Path A needs nothing.** Path B explains the industry cut without Confluence. Path C is your real tenant.

---

## Path A — 60 seconds (offline)

Open this repo root in Cursor:

```text
@requirement-risk DEMO-1 team=demo
@ticket-splitter DEMO-1 team=demo
```

**Done when:** a readiness/risk report with Scope + MUST items, then INVEST slices with `scope` and `done_when`, both grounded in the shipped Acme Orders brief.

Fixture layout: [`domain-knowledge/fixtures/offline-demo/`](domain-knowledge/fixtures/offline-demo/).  
Sample outputs (for comparison): [`docs/demo/`](docs/demo/).  
With vs without brief: [`docs/BENCHMARK.md`](docs/BENCHMARK.md).

No `.env`, no network, no `strategy.md` fill.

---

## Path B — Zero-config industry story (still offline)

Goal: understand **how domain modules are cut** before you touch Atlassian.

| Step | Read / do | Why |
|------|-----------|-----|
| 1 | [`domain-knowledge/strategy.example.md`](domain-knowledge/strategy.example.md) | Filled §2 for fictional **Acme Orders** (format only) |
| 2 | [`domain-knowledge/fixtures/offline-demo/INDUSTRY.md`](domain-knowledge/fixtures/offline-demo/INDUSTRY.md) | Maps example modules → `ordering` brief + `DEMO-1` |
| 3 | Skim the **S7 locale brief** | `fixtures/offline-demo/curated/by-root/100001/_deliver/ordering/ordering-domain-brief.md` |
| 4 | Re-run Path A | Risk/split should cite amend + quote-validity rules from that brief |

You are **not** writing `s2-domain-profiles.json` here. Path B is the mental model:

**strategy §2 → module slug → S7 brief → story review**

### Path B2 — Second industry (still offline)

Prove the cut is not Acme-specific:

```text
@requirement-risk DEMO-BILL-1 team=demo
```

Fixture: [`domain-knowledge/fixtures/saas-billing/`](domain-knowledge/fixtures/saas-billing/) (Northwind Billing · seat proration).  
Industry map: [`saas-billing/INDUSTRY.md`](domain-knowledge/fixtures/saas-billing/INDUSTRY.md).

---

## Path C — Your wiki (credentials)

Shortest real pipeline (use [`FIRST-RUN.md`](.cursor/skills/generate-knowledge-from-wiki/FIRST-RUN.md), not the full RUNBOOK on day one):

1. `cp .env.example .env` and set Atlassian URLs + token
2. `@setup-domain-ops` — fill **your** `strategy.md` §2 → derive profiles → human **confirm**
3. `@generate-knowledge-from-wiki` + your Confluence overview URL → **S1** + **S2** → pause at checklist
4. Mark rows **confirmed** → say **continue** → **S3–S7** Compose
5. After **S7** `*-domain-brief.md` files exist: `@requirement-risk PROJ-123` → `@ticket-splitter PROJ-123`

Install / multi-harness: [`INSTALL.md`](INSTALL.md).  
Pack layout check (no network): `python3 scripts/verify_skills_pack.py`

---

## What “done” looks like

| Path | Done when |
|------|-----------|
| A | Risk report has Scope + MUST items; split has observable `done_when` faces |
| B | You can name Acme’s module axis for “amend open order” without opening Confluence |
| B2 | Risk report for `DEMO-BILL-1` cites Active + proration preview from the billing brief |
| C | Checklist rows **confirmed** → `_deliver/…/*-domain-brief.md` (S7) → risk/split on a real key |
