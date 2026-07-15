# Single Jira issue · domain-knowledge context contract

Chinese locale: [`jira-issue-domain-knowledge-context.zh-CN.md`](./jira-issue-domain-knowledge-context.zh-CN.md).

> **Readers**: Agents for `@requirement-risk`, `@ticket-splitter`, and `@ticket-test-design`.  
> **Sources**: Disk artifacts from [`generate-knowledge-from-wiki`](../skills/generate-knowledge-from-wiki/SKILL.md) ([`RUNBOOK.md`](../skills/generate-knowledge-from-wiki/RUNBOOK.md) Recognize + Compose) and optional [`add-knowledge-from-jira`](../skills/add-knowledge-from-jira/SKILL.md) prep.  
> **Nature**: Paths below are **evidence/context**, **not** a substitute for the `requirement_risk` / `ticket_system` rule bodies.

Layering: [`domain-knowledge-pipeline-contract.md`](domain-knowledge-pipeline-contract.md) §1–§2. Wiki distill detail: [`generate-knowledge-from-wiki/RUNBOOK.md`](../skills/generate-knowledge-from-wiki/RUNBOOK.md).

---

## 1. When loading is mandatory

When analyzing a **Jira issue key** (e.g. `DEV-94211`), **after** reading Jira body/comments/attachments and **before** generating output:

1. Resolve **team** and on-disk **`root_id`** (§2).
2. **Search and read** related domain-knowledge files (§3). If missing, record in `EVIDENCE_COVERAGE` / `source_requirement_note`.
3. **Do not** invent product facts unsupported by the ticket. On conflict, **list both** (ticket vs brief) — do not unilaterally pick a winner.

If the user pastes plain text with no KEY: optional **light keyword search** of configured teams' `curated` when module/system names appear (§3.4); still **do not** assume a team.

If the user sets **`team=<key>`** (`team-roots.json`) or **`root-id=<ID>`**: lock `by-root/<ID>/`.

**Offline demo**: issue key `DEMO-*` (or user declares offline/fixture) → **do not** call Jira; read the fixture tree in [`../skills/_shared/offline-demo.md`](../skills/_shared/offline-demo.md) (`domain-knowledge/fixtures/offline-demo/`).

---

## 2. Resolve team and on-disk root

The team table is **not** a fixed three rows: use `teams` in `domain-knowledge/jira/team-roots.json` (any N keys). Shipped `demo` is an example only. **v3**: Confluence `root_id` / overview / deliver map live on `libraries.*`; each team mounts `libraries[]` (Path C: usually one). Resolvers flatten the primary (first) mount onto `team.root_id` for callers.

| Field | Meaning |
|-------|---------|
| `team` key | Name under `teams` (e.g. `demo`) |
| `libraries[]` | Mounted library keys (ordered; first = primary) |
| `root_id` | On-disk root from primary library → `curated/by-root/<root_id>/` |
| `aliases` | Optional aliases equivalent to the team key |

SSOT: `domain-knowledge/jira/team-roots.json` · resolver: `scripts/teams/registry.py`.

**Resolution order** (stop on first hit):

1. User message `team=` / `root-id=` / display name / alias.
2. Attribution files (try configured roots, or narrow by Jira Agile Team first):

   `domain-knowledge/curated/by-root/<root_id>/jira/attribution/<ISSUE_KEY>.yaml`

   Read `primary`, `themes[]`, `product_line`, `proposition_id` when present.

3. Jira **Agile Team** matched to `team-roots.json` → `jira.agile_team` → `team` + `root_id`.
4. Still unknown: keyword-match summary against each team's `DOMAIN_MODULE_CHECKLIST.md` and `_deliver/` directory names; state **team-inference confidence** in the report.

**On-disk root** is always that `root_id` (shared with `extracted/` and `materialized/`; see pipeline contract §2).

---

## 3. What to read (priority and paths)

Let `R = domain-knowledge/curated/by-root/<root_id>/`, `E = domain-knowledge/extracted/by-root/<root_id>/`, `RULES = domain-knowledge/materialized/by-root/<root_id>/`.

Locale filenames follow `domain-knowledge/language/deliverable-locale-tokens.json` (`deliverable_locale`). Default English: `*-domain-brief.md`, `*-work-draft.md`, `gap-scan.md`.

### 3.1 Handoff (sync metadata)

- `E/PIPELINE_HANDOFF.json` — `root_page_id`, `enumeration_root_page_id`, `distill_quality_bar_doc`, etc.; confirm this sync covers the root.

### 3.2 Directly related to this ticket (highest)

| Condition | Path | Use |
|-----------|------|-----|
| `attribution/<KEY>.yaml` exists | same | Resolve `primary` theme slug |
| `primary` known | `R/_deliver/<slug>/*-domain-brief.md` (S7) | **Business-rule brief** (risk/split boundaries, terms) |
| Same theme ran Jira prep | `R/jira/by-theme/<slug>/` indexes / evidence | Historical implementation posture for the proposition |
| Same theme | theme cluster notes if present | Cluster context (do not copy ticket KPIs) |
| KEY mentioned in theme indexes | search `<KEY>` under `by-theme/<slug>/` | Whether already summarized |

If no **S7 locale brief**: may read `*-source-brief.md` (**S6**), else `*-work-draft.md`, else `_aggregate/<slug>/` (note “not locale brief” / “not S7” in the report); do not treat Recognize aggregates as business commitments.

### 3.3 Cross-cutting

- `R/DOMAIN_MODULE_CHECKLIST.md` — themes marked **confirmed**, main-entry paths.
- `domain-knowledge/language/glossary.md` — terms / module names (**requirement-risk** semantics; **ticket-splitter** / **ticket-test-design** module boundaries).
- `R/_materialization_closure.json` — leaf → curated mapping (find missed source pages).

### 3.4 Deepen on demand (cap reading)

- Jira description has a **Confluence URL** → prefer `RULES/**/*.md` or `E/pages/<pageId>.md`.
- Still thin: limited `rg` under `RULES/` and `R/` (exclude `jira/raw`; suggest ≤15 files) on summary/module names.
- `R/jira/raw/<KEY>.json` — if present and MCP lacks fields, supplement Jira fields (**not** a substitute for live ticket data).

### 3.5 Not business authority

- Full `R/jira/raw/` — do not read through except this ticket's JSON.
- Full `extracted/` tree — only hit pages or handoff-guided single pages.
- Pass placeholders — mean “leaf not distilled”; not rule body.

---

## 4. Write into each skill's output

### requirement-risk

- Add a line under **`EVIDENCE_COVERAGE`**: **Domain knowledge**: paths used; or “unused / no by-root”.
- Findings that **conflict** with the brief: tag **[DOMAIN_KNOWLEDGE]** and cite brief section or slug.
- Contract/boundary gaps already covered by the brief: downgrade to **should clarify** or merge into “aligned with domain library” — **avoid** re-reporting known rules as MUST.

### ticket-splitter

- When `_deliver/<slug>/` exists: **cite** brief acceptance surfaces (User/System/Contract) in `scope` / `done_when`; **do not** split items that contradict explicit out-of-scope in the brief.
- `source_requirement_note`: if Jira vs brief **scope diverge** (e.g. ticket says dev-only, brief requires end-to-end testability), use `ticket_system` INVEST correction format.
- Module splits: anchor on brief **proposition slug / sections**; **do not** invent subsystem names absent from the brief.

### ticket-test-design

- Anchor **given** AC and `scope` / `out` to ticket + brief; **do not** invent UI/API paths or environment capabilities absent from evidence.
- Prefer brief rule clusters for state/eligibility oracles; conflicts → list side-by-side in notes / residual risk (do not silently pick a winner).
- Draft under `.jira_attachments/<KEY>/test_design_draft.md` when KEY present; gate with `validate_ticket_test_design.py`.

---

## 5. Relation to generate-knowledge-from-wiki

- Library **missing** or **stale**: still finish the ticket analysis; note “domain library missing or refresh with `@generate-knowledge-from-wiki`” in evidence — **do not** block output.
- User just synced: trust `PIPELINE_HANDOFF.json` timestamp and `root_page_id`.

---

## 6. Quick search commands (agents)

```bash
# Attribution (replace KEY)
ls domain-knowledge/curated/by-root/*/jira/attribution/KEY.yaml 2>/dev/null

# Locale briefs (English default glob)
ls domain-knowledge/curated/by-root/<root_id>/_deliver/*/*-domain-brief.md
```
