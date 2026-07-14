# add-knowledge-from-jira · Execution Playbook (Agent Must-Read)

> **Locale**: this is the English playbook (English SSOT). Chinese locale: [`RUNBOOK.zh-CN.md`](./RUNBOOK.zh-CN.md).  
> zh-CN deliverable strings (status labels, headings, filenames) come from [`domain-knowledge/language/deliverable-locale-tokens.json`](../../../domain-knowledge/language/deliverable-locale-tokens.json) and are not repeated inline here.

> **Audience**: Cursor Agent (**must** read this file once **Ingest** is complete).  
> **Entry point**: [`SKILL.md`](./SKILL.md) · **Ingest**: [`INGEST-CLI.md`](./INGEST-CLI.md) · **Classify**: [`CLASSIFY-CLI.md`](./CLASSIFY-CLI.md) · **Compose**: [`generate-knowledge-from-wiki/RUNBOOK.md`](../generate-knowledge-from-wiki/RUNBOOK.md)  
> **Contract**: [`../../contracts/domain-knowledge-pipeline-contract.md`](../../contracts/domain-knowledge-pipeline-contract.md) §1, §4 · **Quality bar**: `domain-knowledge/distill-quality-bar.md`

---

## Pipeline Overview (Jira Prep + Unified Compose)

Jira is responsible for supplying business-detail evidence: ACs, comments, status transitions, thresholds, and last-wins decisions. Confluence and Jira differ only at **Ingest/Classify**; once content enters Compose, both must feed into the same **S3→S7 Compose** main line. Jira is no longer treated as a post-S7 patch or an "implementation-notes appendix."

| Stage | Owner | Meaning | Executor | Stop gate |
|------|------|------|--------|------|
| **Ingest** | Jira | Pull tickets → `raw/` (+ optional `materialized/` readable copy) | Script | — |
| **Classify** | Jira | Ticket-level triage → `attribution/`, theme index | Script + Cursor B1 | — |
| **Recognize** | **Shared** | Proposition recognition + closure + human **confirm** | Cursor | **Stop at end of full prep** |
| **Compose** | **Shared** | S3→S4→S5→**S6 source brief**→**S7 locale brief**; S3 reads both Confluence and Jira business evidence | Cursor | Only **confirm**ed rows |

### Prep vs. Compose (stop gates)

| Name | Stage | Executor | Where it stops |
|------|------|--------|--------|
| **Script prep** | Ingest + Classify | `run_jira_knowledge.py` (history pulls up through the current sprint; or `--sprint-id` for a single sprint) | `domain_check jira --full-raw` → **stops** (Agent takes over Recognize) |
| **Full prep** | + Recognize | Cursor (Wiki RUNBOOK · [S2 Recognize](../generate-knowledge-from-wiki/RUNBOOK.md#s2--recognize--repo-wide-tagging-end-of-prep--proposition-level)) | Confirmation page + closure → **stops**, waiting for a human to mark **confirm** |
| **Compose** | Unified Compose | Cursor + Wiki RUNBOOK | Only **confirm**ed rows; `_aggregate/` should show `source_system: jira` |

**Landing root**: `domain-knowledge/curated/by-root/<R>/` (the same `root_id` as Wiki; see `team-roots.json`).

### Comparison with the Wiki Three Stages

| Wiki | Jira |
|------|------|
| Ingest (sync + facet coarse triage) | **Ingest** (fetch; **no** facet directory) |
| Recognize | **Classify attribution** → **Recognize** (shared confirmation gate) |
| Compose (S3→S7) | **Compose** (shared; Jira business tickets are merged in at the S3 input layer) |

### User Phrasing → CLI

| User `mode=` | Agent should run |
|--------------|------------|
| `history` + `team=<t>` | `run_jira_knowledge.py --team <t>`; team maps to a board id, pulling from the earliest sprint through the current sprint (inclusive) |
| `history` + `board-id=<id>` | Map to a team via `team-roots.json`, then run as above |
| `sprint` + `sprint-id` | `run_jira_knowledge.py --team <resolved-team> --sprint-id <id>`; pulls only that sprint |
| `compose` / `continue` | Wiki RUNBOOK Compose; S3 automatically incorporates Jira business tickets |
| `distill` / `reconcile` / `full` | Legacy path removed; refuse to execute and redirect to prep → Recognize → Compose |

### Operation Numbers (Scripts / Gates)

| Stage | Common scripts / docs |
|------|-----------------|
| Ingest | `run_jira_ingest.py` · [`INGEST-CLI.md`](./INGEST-CLI.md) |
| Classify | `run_jira_knowledge.py` · [`CLASSIFY-CLI.md`](./CLASSIFY-CLI.md) |
| Recognize | [Wiki RUNBOOK · S2 Recognize](../generate-knowledge-from-wiki/RUNBOOK.md#s2--recognize--repo-wide-tagging-end-of-prep--proposition-level) |
| Compose | [Wiki RUNBOOK · Compose](../generate-knowledge-from-wiki/RUNBOOK.md#compose--s3--s6-confirmed-topics-only) (S3–S6) |

---

## Ingest · Pull Tickets (Script)

Entry point: `python3 scripts/run_jira_ingest.py` (default is **fetch only** → `raw/`; `--materialize` or `materialize.py` → `jira/materialized/`).

| Strategy | Command | Meaning |
|------|------|------|
| **Specified sprint** | `--mode sprint --sprint-id <id>` | **All** tickets + comments for that sprint |
| **Full board history** | `--mode history --until-complete` | Pulls sprint by sprint from the earliest through the current sprint (inclusive) |

1. Run Ingest; read `jira/JIRA_PIPELINE_HANDOFF.json`.
2. Verify: the count of `jira/raw/*.json` is reasonable (`materialized/` is 1:1 with `raw/` once materialized).
3. Proceed to **Classify** (or run `run_jira_knowledge.py` to run Ingest + Classify + the **Classify gate** together).

For parameters and troubleshooting, see [`INGEST-CLI.md`](./INGEST-CLI.md).

**SSOT**: scripts and attribution read **`raw/`**; `materialized/` is for Cursor closure/human reading (faithful md, **not** authoritative).

---

## Classify · Triage (Script Prep · Jira-Specific)

**CLI parameters / troubleshooting**: [`CLASSIFY-CLI.md`](./CLASSIFY-CLI.md)
**Operating rules**: [`jira_classify.mdc`](../../rules/jira_classify.mdc)

**Purpose**: flat tickets → proposition slugs, an excerpt queue, and a theme index. This is **not** proposition-level domain recognition (that is **Recognize**).

| Action | Output | Executor |
|------|------|--------|
| `python3 scripts/jira/steps/attribute.py --team <t>` | `attribution/<KEY>.yaml`, `_ticket_attribution.json` | Script |
| `python3 scripts/jira/steps/read_business.py --team <t>` | `by-theme/<t>/gap-scan.md` (an **index**; filename follows `deliverable_locale` via `domain-knowledge/language/deliverable-locale-tokens.json` — see the zh-CN locale doc for its non-English filename; themes come from **attribution**, see [`CLASSIFY-CLI.md`](./CLASSIFY-CLI.md)) | Script |
| Cursor rechecks low-confidence attribution | Correct the YAML under `jira/attribution/` | Cursor |
| Optional, once a human marks **confirm** | `read_business.py --confirmed-only` | Script |

**Forbidden**: using ticket-level attribution coverage as a substitute for **Recognize** completion; treating sink slugs (`gateway` / `requirements` or team-configured sinks) as **confirmed** business propositions.

**Classify gate**: `python3 scripts/domain_check.py jira --team <t> --full-raw` (end of script prep)

---

## Recognize · Domain Recognition (End of Full Prep · Shared with Wiki)

Executes [Wiki RUNBOOK · S2 Recognize](../generate-knowledge-from-wiki/RUNBOOK.md#s2--recognize--repo-wide-tagging-end-of-prep--proposition-level): the **same** `DOMAIN_MODULE_CHECKLIST.md`, `_materialization_closure.json`, and human **confirm** marking.

Jira does not re-scan files full-text at S2; instead it maps Classify's `primary`, `themes[]`, `distill_tier`, and `proposition_id` outputs onto the unified confirmation gate. If a mapping is unreasonable, the Agent should correct `attribution/*.yaml` and re-run S2.

| Action | Output |
|------|------|
| `strategy.md` §2 × domain blocks | `DOMAIN_MODULE_CHECKLIST.md` |
| Confluence: scans the S1 manifest/materialized; Jira: reads `attribution/*.yaml` | `_materialization_closure.json` (an **index** — do not paste full text across directories) |
| Non-business pages | Pass placeholder |

**Full-prep-complete report**: Classify index is complete; confirmation page + closure are complete; **no** excerpts / brief yet. **Pause** → human marks **confirm**.

**Recommended gate**: `python3 scripts/distill/coverage.py --root-id <R>`

---

## Human Gate · Domain Module Confirmation

**Identical** to Wiki ([`domain-module-checklist.mdc`](../../rules/domain-module-checklist.mdc)):

| Action | Description |
|------|------|
| Human edits the confirmation page | Approve a row's **"Status"** → **`confirmed`** |
| **`continue`** | Runs unified Compose (S3→S7) on **confirmed rows** |
| No **confirm** yet | **Do not** run Compose |

---

## Compose (Confirmed Topics Only)

**Order**: execute the **Compose** stage (S3→S7) of [`generate-knowledge-from-wiki/RUNBOOK.md`](../generate-knowledge-from-wiki/RUNBOOK.md). S3 proposition extraction reads only sources that S2 closure has already authorized to a confirmed slug; `jira/materialized/<KEY>.md` files and Confluence materialized pages that S2 closure points to that slug enter the same proposition-candidate layer together.

### Compose · Unified Brief Production (Cursor · Mandatory)

**Must** execute [`generate-knowledge-from-wiki/RUNBOOK.md`](../generate-knowledge-from-wiki/RUNBOOK.md) **§Compose** (S3 Aggregate → S4 Domain Model → S5 Work Draft → **S6 Source brief** → **S7 Locale brief**).

S3 admission:

- Confluence: read per `_materialization_closure.json` and already-confirmed slugs.
- Jira: `attribution/<KEY>.yaml`'s `primary/themes[]` hits an already-confirmed slug, and `distill_tier` is `proposition_core` / `platform_variant`.
- Explicitly exclude `engineering_slice`, `cross_theme_ref`, and `index_only`, unless the Agent re-attributes based on business consequence and corrects the attribution.

**Gate**: `python3 scripts/domain_check.py distill --root-id <R>` after **S7**.

---

## Script Orchestration (`run_jira_knowledge.py`)

| Command | Orchestration |
|------|------|
| (no flag) | **Ingest** (from the earliest sprint through the current sprint, inclusive) + **Classify** + Classify gate → **stop gate** (Agent takes over Recognize) |
| `--sprint-id <id>` | **Ingest** (specified sprint only) + **Classify** + Classify gate → **stop gate** |

Ingest-only fine-grained parameters: `python3 scripts/run_jira_ingest.py …`

---

## User Phrasing

| Intent | Phrasing |
|------|------|
| Ingest only · specified sprint | `@add-knowledge-from-jira team=demo mode=sprint sprint-id=1726` |
| Ingest · full board history | `@add-knowledge-from-jira team=demo mode=history` or `board-id=<id> mode=history` |
| Script prep | `mode=history` or `run_jira_knowledge.py` (no flag) |
| Compose (unified brief) | **`continue`** + Wiki RUNBOOK |
| Removed legacy path | `mode=distill/reconcile/full`; refuse to execute and redirect to unified Compose |

---

## Reporting Template

- **Ingest**: sprint id/name, keys in this batch, `jira/raw/` path
- **Classify + Recognize / Full prep**: attribution coverage; confirmation-page **confirmed / pending** row counts; closure
- **Compose**: for each **confirmed** topic: whether `_aggregate/*-propositions.md` shows a Jira source; work draft / brief **present/absent**; whether Jira business detail has been merged into the body rule chains
- **Forbidden**: reporting "Jira pipeline complete" when only attribution or an index exists

---

## Appendix · Step Quick Reference

### Stage ↔ Artifact ↔ Gate

| Stage | Agent must read | Main writes | Gate |
|------|------------|----------|------|
| Ingest | `INGEST-CLI.md` | `jira/raw/`, `jira/materialized/` | script exit code |
| Classify | `CLASSIFY-CLI.md` | `attribution/`, gap-scan index (see note above on its script-emitted filename) | `domain_check jira --full-raw` |
| Recognize | Wiki RUNBOOK · S2 | confirmation page, closure | `coverage.py` (recommended) |
| Compose | Wiki RUNBOOK · Compose | `_aggregate/`, work draft, brief | `domain_check distill` |

### Three Artifact Layers (invariant)

| Layer | Role |
|------|------|
| Index | maps, KEY lists |
| Evidence | `raw/` is the source of record; `attribution/` is the S2 admission basis; `materialized/` is the S3 readable copy |
| Merged | business rule chains within the unified Compose body (not a Jira appendix at the end of the document) |

Historical root cause: see [`pipeline-design.md`](../../../domain-knowledge/jira/pipeline-design.md) §1 — **not** a gate rule.

## Next

`@requirement-risk` → `@ticket-splitter` (evidence: **S7** `_deliver/<slug>/<slug>-domain-brief.md`; zh-CN filename from `deliverable-locale-tokens.json`).
