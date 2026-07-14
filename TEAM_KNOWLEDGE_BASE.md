# Team entry: how to read the domain knowledge base

**Display layer only** — where to start reading. Authoritative process lives in skills and [`.cursor/contracts/domain-knowledge-pipeline-contract.md`](.cursor/contracts/domain-knowledge-pipeline-contract.md).

---

## Authoritative roots (configure yours)

Edit [`domain-knowledge/jira/team-roots.json`](domain-knowledge/jira/team-roots.json) (start from [`team-roots.example.json`](domain-knowledge/jira/team-roots.example.json)):

- **Confluence overview URL** per team
- **`root_id`** → `extracted|materialized|curated/by-root/<root_id>/`

Ships with one demo team (`demo`, root `100001`, placeholder Atlassian URLs). Domain modules are **not** pre-cut — fill [`strategy.md`](domain-knowledge/strategy.md) §2 via `@setup-domain-ops`, then derive profiles before **S2** Recognize.

**Draft (v3):** one Confluence **space** = one **library**; each Jira **team** mounts `libraries[]` — [`docs/TEAM_ROOTS_V3.md`](docs/TEAM_ROOTS_V3.md).

---

## Process tokens (use consistently)

| Token | Meaning |
|-------|---------|
| **confirm** | Human accepts a module-cut row on `DOMAIN_MODULE_CHECKLIST.md` (authorizes Compose for that slug) |
| **continue** | Resume **S3–S7** Compose for **confirmed** rows only |
| **brief** | Short output mode on `@requirement-risk` / `@ticket-splitter` only (summary + coverage, or split overview) — **not** a synonym for S7 |
| **locale brief** / **reader brief** | **S7** `*-domain-brief.md` (deliverable-locale reader doc) |
| **source brief** | **S6** `*-source-brief.md` (source-language adjudication; intermediate) |

Locale-specific spellings for checklist status live in [`domain-knowledge/language/deliverable-locale-tokens.json`](domain-knowledge/language/deliverable-locale-tokens.json). English docs use the English tokens above.

---

## Newcomer path (~30–60 min)

1. **60s offline**: `@requirement-risk DEMO-1 team=demo` — `DEMO-1` is a **shipped fake ticket** (not live Jira); see [`WALKTHROUGH.md`](WALKTHROUGH.md) Path A
2. `@setup-domain-ops` — credentials, teams, **strategy §2**, derive profiles
3. [`domain-knowledge/README.md`](domain-knowledge/README.md) — on-disk layout
4. [`domain-knowledge/strategy.md`](domain-knowledge/strategy.md) — methodology (+ your filled §2)
5. After sync + Recognize + Compose: `curated/by-root/<root_id>/_deliver/<slug>/*-domain-brief.md` (**S7**)

Walkthrough paths: [`WALKTHROUGH.md`](WALKTHROUGH.md).

---

## Story review order

1. [`domain-knowledge/language/glossary.md`](domain-knowledge/language/glossary.md)
2. Relevant **S7 locale brief** (reader brief) under `_deliver/<slug>/*-domain-brief.md`
3. Only then drill into `materialized/` / `extracted/` for evidence

`@requirement-risk` and `@ticket-splitter` read **S7** locale briefs by default. If S7 is missing: optional **S6** `*-source-brief.md`, else work draft (note “not S7” in the report).

---

## Done criteria (internal)

| Layer | Meaning |
|-------|---------|
| Closure | Every materialized leaf maps into curated (`_materialization_closure.json`) |
| Checklist confirmation | Humans mark rows **confirmed** → authorize Compose |
| Briefs shipped | Confirmed slugs have `_deliver/<slug>/*-domain-brief.md` (S7) |

Pipeline runbook: [`.cursor/skills/generate-knowledge-from-wiki/RUNBOOK.md`](.cursor/skills/generate-knowledge-from-wiki/RUNBOOK.md).  
Optional Jira evidence path: `@add-knowledge-from-jira`.

Coverage checks:

```bash
python3 scripts/domain_check.py distill --root-id <YOUR_ROOT_ID>
```
