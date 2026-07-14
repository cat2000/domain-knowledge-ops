# Walkthrough — zero credentials to first value

Three paths. **Path A needs nothing.** Path B explains the industry cut without Confluence. Path C is your real tenant.

---

## Path A — 60 seconds (offline)

Open this repo root in Cursor. Use the **shipped fake ticket** `DEMO-1` (Acme Orders: amend open order while quote is valid) and sample team `demo` — no live Jira, no `.env`:

```text
@requirement-risk DEMO-1 team=demo
@ticket-splitter DEMO-1 team=demo
```

**Done when:** a readiness/risk report with Scope + MUST items, then INVEST slices with `scope` and `done_when`, both grounded in the shipped Acme Orders brief.

Fixture layout: [`domain-knowledge/fixtures/offline-demo/`](domain-knowledge/fixtures/offline-demo/) (`jira/DEMO-1.md` + `ordering-domain-brief.md`).  
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
| 3 | Skim the **reader brief** | `fixtures/offline-demo/curated/by-root/100001/_deliver/ordering/ordering-domain-brief.md` |
| 4 | Re-run Path A | Risk/split should cite amend + quote-validity rules from that brief |

You are **not** writing `s2-domain-profiles.json` here. Path B is the mental model:

**fill strategy → name modules → get a reader brief → story review**

(Agent jargon for the same arc: strategy §2 → slug → **S7** `*-domain-brief.md` → `@requirement-risk`.)

### Path B2 — Second industry (still offline)

Prove the cut is not Acme-specific. **`DEMO-BILL-1`** is another **shipped fake ticket** (Northwind Billing: mid-cycle seat change + proration preview), under [`saas-billing`](domain-knowledge/fixtures/saas-billing/) — still `team=demo`, still no network:

```text
@requirement-risk DEMO-BILL-1 team=demo
```

Fixture: [`domain-knowledge/fixtures/saas-billing/`](domain-knowledge/fixtures/saas-billing/).  
Industry map: [`saas-billing/INDUSTRY.md`](domain-knowledge/fixtures/saas-billing/INDUSTRY.md).

---

## Path C — Your wiki (credentials)

Five **user** actions. Do **not** pre-read the full RUNBOOK. When the agent is mid-run, open [`FIRST-RUN.md`](.cursor/skills/generate-knowledge-from-wiki/FIRST-RUN.md) for the matching step only.

1. **Credentials** — `cp .env.example .env` and set Atlassian URLs + token
2. **Name your cut** — `@setup-domain-ops` — answer org/product/module questions; **confirm** the proposed module list when asked
3. **Point at Confluence** — `@generate-knowledge-from-wiki` + your overview URL — wait for a module checklist (stopping there is success for “prep”)
4. **Approve modules** — mark checklist rows **confirm** → say **continue** — agent writes **reader briefs** under `_deliver/`  
   (Default resume is **continue**. `@distill-domain-knowledge` is advanced: no re-sync / partial step / new chat.)
5. **Review a real story** — `@requirement-risk PROJ-123` → `@ticket-splitter PROJ-123`  
   (`PROJ-123` is a **placeholder** — replace with your real Jira issue key, e.g. `ABC-42`. It is not shipped in this repo.)

| You say / do | What the agent is doing (optional jargon) |
|--------------|-------------------------------------------|
| `@setup-domain-ops` | Fill `strategy.md` §2 → derive profiles |
| `@generate-knowledge-from-wiki` + URL | **S1** Ingest + **S2** Recognize → checklist |
| **confirm** then **continue** | Compose **S3–S7** → reader brief (`*-domain-brief.md`) |
| `@requirement-risk` / `@ticket-splitter` | Read that reader brief as evidence |

Install = **clone this repo**: [`INSTALL.md`](INSTALL.md).  
Pack layout check (no network): `python3 scripts/verify_skills_pack.py`

---

## What “done” looks like

| Path | Done when |
|------|-----------|
| A | Risk report has Scope + MUST items; split has observable `done_when` faces |
| B | You can name Acme’s module axis for “amend open order” without opening Confluence |
| B2 | Risk report for `DEMO-BILL-1` cites Active + proration preview from the billing brief |
| C | Modules marked **confirm** → reader briefs under `_deliver/` → risk/split on a real key |
