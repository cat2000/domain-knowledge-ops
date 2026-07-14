# Walkthrough — zero credentials to first value

Three paths. **Path A** runs DEMO-1 with the domain brief. **Path B** runs DEMO-1 without the brief, then you compare. **Path C** is your real tenant.

---

## Path A — 60 seconds (offline)

Open this repo root in Cursor. Use the **shipped fake ticket** `DEMO-1` (Acme Orders: amend open order while quote is valid) and sample team `demo` — no live Jira, no `.env`:

```text
@requirement-risk DEMO-1 team=demo
@ticket-splitter DEMO-1 team=demo
```

**Done when:** a readiness/risk report with Scope + MUST items, then INVEST slices with `scope` and `done_when`, both grounded in the shipped Acme Orders brief.

Fixture layout: [`domain-knowledge/fixtures/offline-demo/`](domain-knowledge/fixtures/offline-demo/) (`jira/DEMO-1.md` + `ordering-domain-brief.md`).  
Sample outputs: [`docs/demo/`](docs/demo/).

No `.env`, no network, no `strategy.md` fill.

---

## Path B — With vs without a domain brief (still offline, ~10 min)

Keep your **Path A** report. Run the Path B prompt below on the same ticket, then compare the two reports. Checklist of what usually diverges: [`docs/BENCHMARK.md`](docs/BENCHMARK.md).

Optional skim (~2 min): [`INDUSTRY.md`](domain-knowledge/fixtures/offline-demo/INDUSTRY.md) — DEMO-1 → `ordering` brief.

### Path A (with brief) — already ran

```text
@requirement-risk DEMO-1 team=demo
```

### Path B (without brief)

```text
@requirement-risk DEMO-1 team=demo
Path B: use only the Jira/fixture ticket body. Do not read domain briefs, curated/, or fixtures under _deliver/.
```

**Done when:** you can point to at least one concrete difference between the two reports (e.g. invented WMS/API scope vs brief-grounded MUST). Map: [BENCHMARK](docs/BENCHMARK.md).

You are **not** filling `strategy.md` here. Path C builds **your** brief after `@setup-domain-ops`.

### Path B2 — Second industry (optional)

```text
@requirement-risk DEMO-BILL-1 team=demo
```

Map: [`saas-billing/INDUSTRY.md`](domain-knowledge/fixtures/saas-billing/INDUSTRY.md).

---

## Path C — Your wiki (credentials)

**Single library first:** one Confluence space + one Jira board. Config is **v3** (`libraries` + `teams` mounting them) — see [`docs/TEAM_ROOTS_V3.md`](docs/TEAM_ROOTS_V3.md). Copy [`team-roots.example.json`](domain-knowledge/jira/team-roots.example.json) if you need a clean template.

Five **user** actions. Do **not** pre-read the full RUNBOOK. When the agent is mid-run, open [`FIRST-RUN.md`](.cursor/skills/generate-knowledge-from-wiki/FIRST-RUN.md) for the matching step only.

1. **Credentials** — `cp .env.example .env` and set Atlassian URLs + token
2. **Setup** — `@setup-domain-ops` — company/product intro → **confirm** module cut → space overview URL → board id  
   Agent writes `team-roots.json` as **v3** (one `libraries.*` + one `teams.*` with `libraries: [<that key>]`), plus `strategy.md` §2 and profiles
3. **Point at Confluence** — `@generate-knowledge-from-wiki` + your overview URL — wait for a module checklist (stopping there is success for “prep”)
4. **Approve modules** — mark checklist rows **confirm** → say **continue** — agent writes **reader briefs** under `_deliver/`  
   (Default resume is **continue**. `@distill-domain-knowledge` is advanced: no re-sync / partial step / new chat.)
5. **Review a real story** — `@requirement-risk PROJ-123 team=<your_team>` → `@ticket-splitter PROJ-123`  
   (`PROJ-123` is a **placeholder** — replace with your real Jira issue key, e.g. `ABC-42`. It is not shipped in this repo.)  
   Optional Jira evidence: `@add-knowledge-from-jira team=<your_team>`

| You say / do | What lands on disk |
|--------------|-------------------|
| `@setup-domain-ops` | v3 `team-roots.json` + `strategy.md` §2 + profiles |
| `@generate-knowledge-from-wiki` + URL | **S1** Ingest + **S2** Recognize → checklist under `by-root/<root_id>/` |
| **confirm** then **continue** | Compose **S3–S7** → reader brief (`*-domain-brief.md`) |
| `@requirement-risk` / `@ticket-splitter` | Read that reader brief as evidence |

Install = **clone this repo**: [`INSTALL.md`](INSTALL.md).  
Pack layout check (no network): `python3 scripts/verify_skills_pack.py`

---

## What “done” looks like

| Path | Done when |
|------|-----------|
| A | Risk report has Scope + MUST items; split has observable `done_when` faces |
| B | Path B (without brief) report differs from Path A on at least one concrete point |
| B2 | Risk report for `DEMO-BILL-1` cites Active + proration preview from the billing brief |
| C | Modules marked **confirm** → reader briefs under `_deliver/` → risk/split on a real key |
