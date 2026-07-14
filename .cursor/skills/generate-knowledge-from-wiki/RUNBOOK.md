# generate-knowledge-from-wiki · Execution Playbook

> **Locale**: English playbook (English SSOT). Chinese: [`RUNBOOK.zh-CN.md`](./RUNBOOK.zh-CN.md).  
> All zh-CN deliverable strings (status labels, headings, filenames) come from [`domain-knowledge/language/deliverable-locale-tokens.json`](../../../domain-knowledge/language/deliverable-locale-tokens.json) — this file cites **English** labels/tokens only and does not repeat the zh-CN strings inline.

> **Do not read this file end-to-end on first run.**  
> Start: [`FIRST-RUN.md`](./FIRST-RUN.md) + [`SKILL.md`](./SKILL.md).  
> Then open **only the S\* section you are executing**. Compose disputes → [`references/iron-laws.md`](./references/iron-laws.md).  
> Scripts: [`S1-SYNC-CLI.md`](./S1-SYNC-CLI.md) · Contract: [`../../contracts/domain-knowledge-pipeline-contract.md`](../../contracts/domain-knowledge-pipeline-contract.md) §1–§2.

### Jump by step

| Step | Section below |
|------|----------------|
| Overview | [Three-Stage Overview](#three-stage-overview-master-narrative) · [S1–S7 table](#seven-step-operation-numbering-s1s7) |
| S1 | Search headings containing `S1` / Ingest |
| S2 | Search `Recognize` / confirmation page |
| S3–S7 | Search `S3` / `S4` / `S5` / `S6` / `S7` / Brief |
| Appendix | [Appendix · Step Quick Reference](#appendix--step-quick-reference) |

---

## Three-Stage Overview (Master Narrative)

Externally, the Confluence pipeline is described as **three stages**; **S1–S7** are the Agent's internal **operation numbers** (gates, artifact paths, and reporting still use S*).

| Stage | Meaning | Corresponding step | Executor | Stop gate |
|------|------|--------|--------|------|
| **Ingest** | Sync + facet materialization (**coarse machine triage**) | **S1** | Script | — |
| **Recognize** | Proposition-level domain recognition + closure + human **confirm** (checklist status → `confirmed`) | **S2** | Script (Agent reviews) | **Stop at end of prep** |
| **Compose** | Aggregate → domain model → work draft → **source brief** → **locale brief** | **S3 → S4 → S5 → S6 → S7** | S3 = script; S4–S7 = Agent | Only **confirm**ed rows |

- **Prep** = **Ingest + Recognize** (S1 + S2) → **pause** (human reviews the confirmation page)
- **Compose** = S3 → S7; after the user says the **continue** keyword, it can be run in batches by slug

Compose sub-steps: **S3 Aggregate** → **S4 Domain Model** → **S5 Work Draft** (all **no translation**) → **S6 Source brief** (adjudicated reader structure in **source language**) → **S7 Locale brief** (expression-only conversion to `defaults.deliverable_locale`; risk/split read this file).

---

## Seven-Step Operation Numbering (S1–S7)

| Step | Stage | Name | Executor | Artifact | Language |
|----|------|------|--------|------|------|
| **S1** | Ingest | Sync | Script | `extracted/`, `materialized/` | source language |
| **S2** | Recognize | Recognize & tag | Script (Agent reviews) | **Domain module confirmation page**, `_materialization_closure.json` | unmodified |
| **S3** | Compose | Aggregate | Script | `_aggregate/<slug>/` | source language |
| **S4** | Compose | Domain model | Agent | the `## Domain model` section inside `_deliver/<slug>/<slug>-work-draft.md` | matches source |
| **S5** | Compose | Work draft | Agent | `_deliver/<slug>/<slug>-work-draft.md` | matches source |
| **S6** | Compose | Source brief | Agent | `_deliver/<slug>/<slug>-source-brief.md` | **source language (no translation)** |
| **S7** | Compose | Locale brief | Agent | `_deliver/<slug>/<slug>-domain-brief.md` (filename per `defaults.deliverable_locale`; see `deliverable-locale-tokens.json`) | **`deliverable_locale`** |

### Responsibility Boundaries (Skill vs. Script)

| Step | Skill/Agent primary responsibility | Script primary responsibility |
|---|---|---|
| S1 | Contract: input boundaries, no translation, no semantic rewriting | Execution: sync, materialization, coarse triage |
| S2 | Contract: confirm semantics, human gate, review actions | Execution: recognition, closure, ledger, blocking |
| S3 | Contract: fidelity-preserving triage, deferred adjudication, decision-contract fields | Execution: extraction, normalization, indexing, minimal audit view |
| S4 | Contract: domain model (objects/states/actions/relationships/containers/field anchors) | Execution: model-structure gate; does not generate body text |
| S5 | Contract: rule chains attached to the model, explicit conflicts | Execution: work-draft quality gate; does not generate body text |
| S6 | Contract: source-language brief structure (adjudication complete; **no translation**) | Execution: structural gates; does not generate body text |
| S7 | Contract: locale expression conversion only (**no new semantics**) | Execution: gates, regression, reporting |

Boundary rules:
- Scripts perform deterministic processing only; they never adjudicate business rules.
- Scripts must not fall back to text templates for S4/S5/S6; a missing draft must fail explicitly.
- The Agent owns adjudication and narrative; it must not substitute manual patches for process-level fixes.

### Deprecated Legacy Paths (must be enforced)

- Deprecate the reverse dependency `S6 -> decision_atoms -> S5/S4`; S3 is a structured-evidence source, not a business-adjudication source.
- Deprecate auto-filled `WORK_DRAFTS` / `FINAL_DRAFTS` main-path defaults in the Compose orchestrator.
- If S4/S5/S6 files are missing, the orchestrator must error and stop — scripts are never allowed to ghost-write body text.

### S1 vs. S2 Division of Labor (do not treat the two steps as duplicate domain recognition)

| | **S1 · Sync** | **S2 · Recognize & tag** |
|---|----------------|---------------------|
| **Nature** | **Coarse machine triage** (script, no LLM) | **Proposition-level domain recognition + closure + human confirm** |
| **What it does** | REST extraction; `facet_classify` writes into `facet-*/` by title/summary keywords | Uses the unified source registry for proposition-level recognition: reads S1 manifest/materialized for Confluence, reads attribution for Jira; refreshes the confirmation page and closure; the previous round's `glossary.md` is only a lightweight synonym reference |
| **Artifacts** | `extracted/`, `materialized/by-root/<R>/facet-*/` | `DOMAIN_MODULE_CHECKLIST.md`, `_materialization_closure.json` |
| **Not yet done when** | `facet-*` **≠** confirmed domain block; **≠** brief | checklist marked **confirm** **≠** a Chinese-language brief already exists |

S1's `facet-checkout/` and the like are **materialized-directory heuristics**, not the **confirmed slugs** in the checklist. S2 **must** explicitly tag closure, and **must not** report "module covered" purely from a facet directory name — for example `facet-unmatched/` (see §S2 Forbidden).

### Compose Objective Function (S4–S7 · Priority Order)

When executing **S4 / S5 / S6 / S7**, use [`distill-quality-bar.md`](../../../domain-knowledge/distill-quality-bar.md) **§Objective Function** as the arbiter (the detailed rules apply together with that same file's §Pre-Draft Triage and §Forbidden sections):

1. **Domain modeling** — first identify domain objects, states, actions, state changes, display containers, and field anchors, then attach rule chains; going straight to piling up a rule list is the **wrong** target.
2. **Isolate business noise** — collaboration scheduling, pure ticket matrices, DDL/SQL/Git, and field seas without business explanation → triage these out of the main decision chain as supporting material/noise; never let them pass as business rules.
3. **Comprehensive (business side)** — any clause affecting "should this happen, will it produce a visible consequence for users/advisors" must be **written in full and verifiable**; merge duplicates, and it is **forbidden** to substitute "see materialized for details" for an entire rule chain.
4. **Language** — **no translation in S4/S5/S6**; **only S7** produces the target-locale brief (`deliverable_locale`).

- **Domain module confirmation page** = `DOMAIN_MODULE_CHECKLIST.md`; **"Status" = `confirmed`** authorizes **Compose**.
- **`confirm` ≠ brief already produced**; brief completion = **S6 source brief** + **S7 locale brief** (risk/split read S7).
- **Forbidden**: in-repo HTTP LLM API calls; **S1–S6 forbid** full-text translation.
- By default, `@generate-knowledge-from-wiki` = **prep** (Ingest→Recognize / S1→S2) → **pause**; once rows are marked **confirm**, say **continue** to run **Compose** (S3→S7, which can be batched by slug).
- **Landing root**: `extracted/by-root/<R>/PIPELINE_HANDOFF.json` → `root_page_id`.

---

## S1 · Sync (Script · Coarse Machine Triage)

Inside the script: `extract` → `facet_classify` → `materialize`. Produces **faithful source text** + a **`facet-*` directory** (keyword heuristics for S2 to scan, **not** a proposition-level final answer).

S1 must be complete by default: if `_last_extract_report.json` contains any page error, S1 stops there — no complete handoff is written, and it does not proceed to S2. Only once a human has explicitly accepted the risk of missing pages may `--allow-partial` be added to write a handoff with `s1_status=partial`.

S1 materialization must reflect the current source set: `materialized/by-root/<R>/_materialized_manifest.json` is the generated manifest; during materialization, old `.md` files no longer produced by the current extraction pages are deleted, to keep stale material from polluting S2.

S1's coarse triage only executes profile configuration: facet keywords and explicit noise titles come from `domain-knowledge/s2-domain-profiles.json`; scripts must not hard-code team- or historical-page-specific exceptions.

**Strategy-first**: if `checklist_themes` is empty, **hard-stop** — first run `@setup-domain-ops` to fill in [`strategy.md`](../../../domain-knowledge/strategy.md) §2 and derive profiles, then run S1/S2. An empty-shell repo provides no industry-default modules.

```bash
python3 scripts/sync_domain_knowledge_from_confluence.py --url "<PAGE_URL_OR_ID>"
```

1. Run it; read the **HANDOFF** → landing root `<R>`.
2. Otherwise proceed to **S2** (proposition-level recognition, see the table above).

For parameters and troubleshooting, see [`S1-SYNC-CLI.md`](./S1-SYNC-CLI.md).

---

## S2 · Recognize + Repo-Wide Tagging (End of Prep · Proposition-Level)

**Purpose**: on top of S1's coarse triage and Jira Classify, fully recognize **domain proposition blocks**; every source under acceptance has a landing spot in closure; refresh the **domain module confirmation page** and wait for a human to mark **confirm**.

**Prerequisite**: the `checklist_themes` in `s2-domain-profiles.json` must already be derived from strategy and human-confirmed; otherwise hard-stop and redirect to `@setup-domain-ops`.

**On first recognition / when switching team roots / when the module table is too coarse / when the page count changes significantly after an S1 rescan**, you may first run **module proposal** (path B) to assist human review, then update the profile, then recognize:

```bash
# team is resolved from root-id via team-roots.json; module_seeds is filtered by teams[] (may be empty, in which case rely on the Wiki tree alone, requiring stronger human review)
python3 scripts/distill/s2_propose_modules.py --root-id <R> --write-checklist-draft
```

- Reads the Confluence **Wiki tree** (REST BFS, requires `.env` credentials) + **`s2-propose-industry-seeds.json`** (derived from `strategy.md` §2; may be empty by default in open source) + S1 facet/titles
- Produces **`S2_PROPOSED_MODULES.json`**, **`S2_PROPOSED_MODULES.md`** (and optionally **`DOMAIN_MODULE_CHECKLIST.proposed.md`**, all with status **`pending`**)
- After **human review**, write the confirmed slug/cues into **`s2-domain-profiles.json`** (root profile or `profiles_by_team.<team>`), which must be consistent with `strategy.md` §2, then run recognize below

S2 recognize (once the profile is ready):

```bash
python3 scripts/distill/s2_recognize.py --root-id <R>
```

This script outputs:
- `DOMAIN_MODULE_CHECKLIST.md`
- `_materialization_closure.json`
- a non-business appendix index (fixed script-emitted path under `_appendix/`, collecting non-business pages)
- `S2_DECISION_LEDGER.json` (machine-recognition ledger)
- `S2_REVIEW_DECISIONS.json` (human-adjudication ledger)
- `S2_RECALL_REVIEW.md` (suspected-missed-recognition list, for human confirmation)

| Action | Output |
|------|------|
| `strategy.md` **domain proposition ruler** × the unified source registry | `curated/…/DOMAIN_MODULE_CHECKLIST.md` |
| Confluence: reads `materialized/by-root/<R>/_materialized_manifest.json` (falls back to scanning materialized if missing) | `curated/…/_materialization_closure.json` |
| Jira: reads `jira/attribution/*.yaml` / `_ticket_attribution.json`, mapped by `primary/themes[]/distill_tier` | same closure + confirmation page (**index paths only** — do not paste full text across directories) |
| Non-business pages | placeholder + a non-business determination note heading (script-authored); **excluded from Compose** |

**Forbidden**: full-text translation; **duplicate-pasting** the same `materialized/` source text across multiple output directories; treating S1's **`facet-*` directory names** (e.g. `facet-checkout/`, `facet-unmatched/`) as domain proposition slugs.

**Preventing missed scattered material**: on the Confluence side, besides classifying `materialized/` by proposition per `strategy.md`, you must also run a full-text search over `materialized/` and semantically fill in gaps; on the Jira side, do not re-scan files full-text for recognition — instead use Classify attribution as the source registry, with the Agent correcting the YAML when necessary. Gap-filling paths are written into `_materialization_closure.json` and the **domain module confirmation page**. The previous round's stable `glossary.md` may only serve as a synonym/abbreviation hint, and its completeness must not be relied on to decide domain boundaries; newly discovered terms in this round are only written into the confirmation page's **terminology notes**, to be folded into the glossary after S6.

**Primary-facet re-check**: S1's `facet-*` is only a coarse-triage default, not the final adjudication of the domain slug. Even when it hits `primary_facet_to_slug`, S2 must still perform a cross-slug re-check using page-title/path-level `route_overrides`; re-assign only when the title/path explicitly points to another confirmed slug — an incidental word in the body must not trigger a cross-slug handoff.

Confirmation-page rules: [`domain-module-checklist.mdc`](../../rules/domain-module-checklist.mdc) · Template: [`DOMAIN_MODULE_CHECKLIST.template.md`](../../../domain-knowledge/DOMAIN_MODULE_CHECKLIST.template.md) (one field-block per module — not wide tables).

**Prep-complete report**: confirmation page + closure are both in place; **no** `_aggregate` / brief yet. Then **required**:

```bash
python3 scripts/distill/tagging_acceptance.py --root-id <R>
```

Show `TAGGING_ACCEPTANCE.md` to the human. **Pause** → human marks **confirm** only for rows the report allows. **Do not** instruct “confirm all modules.”

If `board_id` is configured and the report shows Jira attribution = 0, recommend `@add-knowledge-from-jira team=<key>` (or ingest+classify), then re-run S2 + tagging acceptance before compose.

**Post-S2 gate (recommended)**: `python3 scripts/distill/coverage.py --root-id <R>`

**Compose hard gate**: if any of the following is true, `proposition_extract.py` blocks S3 by default (requires explicit `--allow-unconfirmed` to override):
- `DOMAIN_MODULE_CHECKLIST.md` still has rows marked `pending`

---

## Human Gate · Domain Module Confirmation

| Action | Description |
|------|------|
| Human edits the confirmation page | Set module **Status** → **`confirmed`** (field-block layout) **only when** tagging acceptance says OK (tagged Confluence/Jira sources in closure). Zero-source rows stay **`pending`**. |
| **`continue`** | Runs **S3→S7** on **confirmed rows** (can be scoped to a slug) |
| No **confirm** yet | **Do not** run S3 / S4 / S5 / S6 |

**Empty evidence**: if Note / tagging report says no tagged sources (or `pages_with_props=0` after S3), **do not** mark **confirm**. Leave pending. Confirming an empty module is a process failure, not a shippable brief.

**Low evidence**: optional confirm only if intentional; S7 must open with an **Evidence insufficiency** banner and list residual gaps under Open items; `@requirement-risk` must treat that brief as non-SSOT in `EVIDENCE_COVERAGE`.

On rescan, **merge incrementally**; **preserve** manually marked **confirm**. S2 refreshes **Note** from Status + source count (clears stale “awaiting human confirm” once Status is confirmed).

---

## Compose · S3 → S6 (Confirmed Topics Only)

### S3 · Aggregate (Compose ①)

| Output | Rule |
|------|------|
| `_aggregate/<slug>/` | Performs fidelity-preserving triage, provenance indexing, and structured hand-off for confirmed modules, preserving the source language; no reader-facing rewriting or business adjudication |

S3.5 (new, script-based proposition intermediate layer):

- First run `python3 scripts/distill/proposition_extract.py --root-id <R>` (optionally `--only-slug`)
- Artifacts:
  - `_aggregate/<slug>/<slug>-propositions.json` (per-page structured candidate propositions)
  - `_aggregate/<slug>/<slug>-propositions.md` (human/Agent-reviewable draft; sibling of the JSON above)
  - `_aggregate/CROSS_SLUG_HANDOFF.json|md` (audit list of S2 primary-facet cross-slug handoffs; an empty list is still generated when there are no handoffs)
- Source set: reads only sources in S2's `_materialization_closure.json` that point to confirmed slugs; Confluence paths resolve to `materialized/by-root/<R>/`, Jira paths resolve to `curated/by-root/<R>/jira/materialized/`; S3 is forbidden from re-deciding admission by `facet-*`, Jira attribution, or directory scanning.
- Constraint: S4/S5 should consume this proposition list preferentially, rather than directly rewriting page summaries.
- Cross-slug constraint: S4/S5 must check `_aggregate/CROSS_SLUG_HANDOFF.md`; for handed-off pages, the target slug must explicitly absorb, demote, or exclude them — a page must not silently disappear just because it originally lived in a different `facet-*` directory.
- Requirement: each `proposition_item` should, wherever possible, produce a `decision_block` (object/condition/action/consequence/threshold/time window/exception) and a `decision_confidence`, for S4 modeling and S5 rule-chain attachment.
- Fidelity-triage contract (mandatory):
  - Page-level: `doc_intent` (`rule_spec` / `api_contract` / `release_change` / `test_ops` / `discussion_decision`)
  - Page-level: `structured_source` — when S1 contains a long mapping table, field table, state-enum table, eligibility/tier/reward table, time-window table, or visible-copy table, the structural signal, header/fields, dense-row count, and sample rows must be recorded; this is not a business adjudication, only a safeguard against long tables being lost because any single-row proposition looks weak
  - Proposition-level: `candidate_type` (`contract_candidate` / `evidence_note` / `noise_context`) + `eligibility_reason`
  - Fidelity-level: `semantic_roles` / `semantic_preservation_reason` / `business_scope_label`
  - Evidence-level: `scope_id` / `scope_label` + `evidence_span`
  - Orchestration-level: `decision-atoms` consumes only `contract_candidate`, and only as a minimal audit view; `evidence_note` is retained as deferred-adjudication evidence for S4; `noise_context` does not re-enter S4 attachment by default
- Causality-priority contract (new):
  - Proposition-level must add `decision_track` (`decision_core` / `presentation_context` / `unresolved_critical` / `noise_context`)
  - Proposition-level must add `causality_score` (used to prioritize "decidable causality")
  - `unresolved_critical` represents high-value but not-yet-adjudicated items; weakening or absorbing these in S4/S5/S6 is forbidden
  - S3 is forbidden from inferring branches based on threshold magnitude, local samples, or implied business knowledge; it must only preserve the source material's explicit structure — business meaning is re-attached by the S4/S5 Agent
- Single-stage admission:
  - Admission to `contract_candidate` is decided only by `decision_track + causality_score + signal + fields`
  - `presentation_context` enters `evidence_note` for deferred adjudication; `noise_context` writes an `admission_drop_reason` and is then isolated
  - Document type (`doc_intent`) is only a threshold prior and **cannot** directly veto a high-causality proposition
- High-confidence trigger gate (to avoid false kills):
  - `proposition_quality` performs hard validation on `doc_intent`/`candidate_type` (field validity, consistency, missing values)
  - The intent-triage ratio gate only triggers a hard failure when there is "strong title match + sufficient sample size" (e.g., excessive contract leakage on release pages)
  - Amplifying heuristic `doc_intent` error directly into a full-pipeline failure is forbidden

**After S3 (required before drafting S6/S7):**

```bash
python3 scripts/distill/tagging_acceptance.py --root-id <R> --after-s3
```

Compare closure counts vs `pages_with_props` vs (later) S7 rule counts. Under-write → Open items or do not claim the module is fully covered. `pages_with_props=0` → do not ship a committed S7.

S3.6 (minimal derived audit view):

- Run `python3 scripts/distill/decision_atom_sync.py --root-id <R>`
  - Artifact: `_aggregate/<slug>/<slug>-decision-atoms.json|md`
  - Purpose: generates a minimal cross-check view (object/condition/branch/consequence/time window/exception/evidence) from `contract_candidate`; it does not replace the S4 domain model or S5 semantic re-attachment
- Run `python3 scripts/distill/conflict_ledger_sync.py --root-id <R>`
  - Artifact: `_aggregate/<slug>/<slug>-conflict-ledger.md`
  - Purpose: makes conflicts explicit (adjudicated / pending); the body text must not silently override prior wording

Pass / non-domain content: **skip S3**.

### S4 · Domain Model (Compose ②)

| Output | Rule |
|------|------|
| the `## Domain model` section inside `_deliver/<slug>/<slug>-work-draft.md` | identifies domain objects, states/phases, business actions, state changes, display containers, and field anchors; **no translation** |

S4 domain-model minimum requirements (inherited by S5):

- Identify **first-class business objects**: business objects, not pages/APIs/fields/metrics/boundary material.
- Identify **metrics/fields**: formulas, progress, amounts, targets, API fields, enum values, and other measurable or carrier fields.
- Identify **display containers**: cards, lists, detail pages, page regions, API responses, and other carrier layers.
- Identify **object relationships**: dependency, carrying, computation, display, drill-down, or prerequisite relationships between objects.
- Identify **state machines/state transitions**: what states the core object moves between, or how eligibility/amount/display changes.
- Identify **boundary candidates**: excluded material, topics pending migration, release/compliance/engineering support, etc. — must not be mixed into first-class business objects.

S4 output structure (mandatory):

- `## Domain model`: list, layered by `First-class business objects`, `Metrics/fields`, `Display containers`, `Object relationships`, `State machines/state transitions`, and `Boundary candidates`.
- UI/API/fields/metrics/formulas may only land in `Metrics/fields` or `Display containers`, never as a first-class business object.
- If a high-value piece of evidence cannot be attached to any domain object, S5's pending-adjudication section must state its `Linked prerequisite domain` and `Decision impact`.

S4 MUST (Skill is the primary definition; the script only validates):

- The Agent must first read `_aggregate/<slug>/<slug>-propositions.json` and `*-propositions.md`; `decision-atoms` may only assist cross-checking and must not be used as the primary generation source.
- The Agent must first judge the first-class business objects in the source material per `strategy.md` / `distill-quality-bar.md`: objects, conditions, business branches, states/phases/tiers, eligibility, rewards, display rules, thresholds, time windows, user-visible impact.
- Named business structures must be preserved: named branches, phases, paths, tiers, levels, states, cycles, markets, cards, etc. in the source material must enter the main chain or the pending-adjudication area whenever they carry business-adjudication or visible-consequence meaning — they must not be abstracted into an unnamed condition and disappear.
- The Agent must demote pages, endpoints, fields, cards, dialogs, and lists to evidence locations, field anchors, or display containers.
- The Agent must use the model to first explain "what objects and states this domain is composed of," before letting S5 write rule chains; piling up chains directly from source subsections is forbidden.
- Script gate: `python3 scripts/distill/domain_model_quality.py --root-id <R>` only validates model structure, whether S5 chain objects inherit S4's first-class business objects, and whether fields/APIs/pages have been demoted; it must not generate or replace S4's semantic body text.

### S5 · Work Draft (Compose ③)

| Output | Rule |
|------|------|
| `_deliver/<slug>/<slug>-work-draft.md` | attaches rule chains based on the S4 domain model, makes conflicts explicit, writes the business side in full (objective function 1–3); **no translation** |

Before drafting S5/S6, you must first read [`domain-knowledge/distill-authoring-contract.md`](../../../domain-knowledge/distill-authoring-contract.md). That file defines the minimal authoring contract that passes the gates; this RUNBOOK defines the semantic principles and process.

S5 minimum requirements per rule chain:

- `Domain object`: must come from `First-class business objects` in `## Domain model`
- `State change`
- `Business action`
- `Display containers/field anchors`: may only reference `Metrics/fields` or `Display containers` in the model
- Explicit **applicable subject** (who)
- Explicit **trigger condition** (when it takes effect, including thresholds/time windows/state)
- Explicit **branch or action** (how it is handled)
- Explicit **user-visible impact** (what visible impact it has on users/advisors)
- At least 1 **concrete anchor**: one of a numeric value, state transition, API/field token, time window, or enum value

S5 output structure (mandatory):

- `## Overview & scope`: describes, in business language, the domain objects, scope, and reader questions covered by this draft; S5 is already a domain-knowledge work draft and must not contain only input disposition and chain tables.
- `## Input disposition summary`: explains how this draft dispositions `contract_candidate` / `evidence_note` / `noise_context`; must separately list the disposition of high-value evidence (formulas, thresholds, state enums, display mappings, card visibility, time windows, eligibility/reward/amount consequences, user-visible fields): into a closed chain, split as a half-closed item, pending adjudication, or the reason for exclusion
- `## Domain model`: carries forward the S4 layered model; every closed-loop chain must attach to a first-class business object within it, and may reference metrics/fields and display containers.
- `## Ordering rationale`: before the closed-loop chains, write, chain by chain, in final drafting order, `Chain N: <title> — <ordering rationale>`; used to prove that S5 has converted source order/API order/UI order into business-adjudication order
- `## Closed-loop decision chains`: carries only rule clusters where `decision_track=decision_core`
- `## Pending-decision critical issues`: carries `decision_track=unresolved_critical`, writing for each item "linked chain / linked prerequisite domain / decision point / current evidence / pending confirmations / decision impact"
- `## Structured detail handoff` (conditional): must appear whenever an S3 proposition, an S3 page-level `structured_source`, or S5 semantic re-attachment discovers a mapping table, state enum, field list, formula/threshold table, time-window table, visible-copy list, or numbering/tier/level mapping; first adjudicate via the "three-way split" into full expansion, rule-compressed, or pending-confirmation, then split into `###` subsections by business rule, preserving queryable detail via tables or indented lists, as the sole source for S6's `## Key details`
- `presentation_context` serves only as supporting information and must not pass itself off as the main decision chain
- Delivery/collaboration/acceptance-cadence material (e.g., beta builds, bug lists, sprint/retro, commit frequency, three-party collaboration, phase-acceptance dates) is, by default, boundary or supporting evidence; it may only be written into a closed-loop chain when it directly changes a business object's user-visible commitment, and the delivery context must be demoted to a display/quality impact.
- Half-closed material must be split: the clearly stated business rule is written into the closed-loop chain, while the not-yet-specified implementation/API/field/detection method is written into the pending-adjudication area; the closed-loop chain must state `Linked open items: Issue N`.
- The input-disposition summary must state the semantic-normalization outcome for duplicated/cross-UI-container/cross-API-field items: merged into the primary rule, demoted to a field anchor, listed as a display location, or moved into pending adjudication.
- The input-disposition summary should only state the ordering-normalization principle, without a second, separate detailed chain order; the detailed chain order is authoritative only in `## Ordering rationale`, to avoid two conflicting orderings in the same draft.

S5 MUST (Skill is the primary definition; the script only validates):

- The Agent must first read the S4 domain model, `_aggregate/<slug>/<slug>-propositions.json`, and `*-propositions.md`; `decision-atoms` may only assist cross-checking and must not be used as the primary generation source.
- The Agent must disposition `contract_candidate` / `evidence_note` / `noise_context` by category: into a closed-loop chain, into pending adjudication, as supporting evidence, or excluded as noise.
- The Agent must perform a high-value-evidence uplift scan: whenever evidence contains a formula, threshold, state enum, display mapping, card visibility, time window, eligibility/reward/amount consequence, or user-visible field, it must be uplifted into a closed-loop chain, a half-closed chain, or a pending-adjudication question even if it is not a `contract_candidate`; it is forbidden to demote it to supporting material merely because S3 did not accept it as a contract.
- The Agent must perform structured-detail hand-off: whenever a table, enum, field list, numbering mapping, state window, or threshold/formula list within high-value evidence or a page-level `structured_source` is useful for reader lookup, it must enter `## Structured detail handoff` even if it does not fit into a closed-loop main sentence; it is forbidden to say "normalized" in the input-disposition summary and let the detail simply vanish.
- The Agent must adjudicate the hand-off method using S5's three-way detail-granularity split:
  - **Full expansion**: readers need to look up or judge item by item; each row could change identity, eligibility, reward, state, field meaning, time window, visible copy, or exception; the row count is bounded and the source is stable. Output a table preserving key columns, row identifiers, source names, and exceptions/notes.
  - **Rule-compressed**: source rows are highly homogeneous and can be losslessly generated from a stable formula, sequential numbering, an arithmetic-step threshold, a fixed naming pattern, or an explicit range; no single row carries an independent exception meaning. Output the range, generation rule, endpoints, step size, exceptions, and at least 1-2 examples; it is forbidden to write only "several/many/related."
  - **Pending confirmation**: the source conflicts, is incomplete, only provides a design-mockup placeholder, has an unclosed field meaning, has unconfirmed user-visibility, or has an unstable display location/scope. It must not be dressed up as a full expansion; it enters `## Pending-decision critical issues` or S6's `## Pending confirmations`, stating clearly what material is missing and its impact once supplied.
- The Agent must identify half-closed items: when the business rule is clear but the implementation/API/field/detection method is not, it must not be entirely downgraded to pending adjudication, nor entirely upgraded to a full commitment.
- The Agent must perform semantic normalization: a single closed-loop chain may correspond to only one business-adjudication object; pages, endpoints, fields, cards, dialogs, and lists are only evidence locations, field anchors, or display containers. When the same business action appears in multiple containers, write it as one primary rule and list "display location/field anchor/evidence source" within the chain.
- The Agent must perform ordering normalization: the same-page order in S1 only represents the source's presentation order, and cannot automatically be treated as the business execution order. If the source order reflects the business process, S5 preserves and explains it; otherwise reorder by `admission/eligibility -> prerequisite check -> core adjudication/computation -> settlement/state posting -> display/operations -> placeholder backfill`.
- The Agent must write the ordering plan before writing closed-loop chains; each closed-loop chain's `### Chain N: <title>` must match the chain number, title, and order given in `## Ordering rationale`.
- The Agent must keep the whole draft structurally consistent: the domain overview and input-disposition summary summarize in ordering-plan order; pending-adjudication questions are arranged in the order of their associated chains, and each question must state `Linked chain: Chain N` or `Linked prerequisite domain: ...`, and must state `Decision impact`.
- The Agent must keep cross-links consistent: when a closed-loop chain writes `Linked open items: Issue N`, `Issue N` must exist, and that issue block must link back to the chain; a chain must not point to an unrelated issue.
- The Agent must keep domain boundaries demoted: excluded material, noise, engineering collaboration, release/compliance support, topics pending migration, and unattributed material must not be written as a `Domain object`; they may only be written into the input-disposition summary, a pending-adjudication upstream domain, or an exclusion note.
- The Agent must keep delivery context demoted: beta builds, bug lists, sprint/retro, commit frequency, three-party collaboration, project start/completion dates, and phase-acceptance dates must not enter the core rules of `## Closed-loop decision chains`; if they affect user-visible quality, they may only be written as a boundary candidate, a pending-adjudication question, or display-quality supporting evidence.
- The Agent must perform model layering: first-class business objects, metrics/fields, display containers, object relationships, state machines/state transitions, and boundary candidates must be written separately; progress, formulas, amount fields, API tokens, and page cards must never be written as first-class business objects.
- The Agent must perform model-to-chain consistent attachment: a closed-loop chain's `Domain object` must be selected from `First-class business objects`; if a rule actually revolves around a metric, formula, amount, field, page, or card, it must be attached to the first-class business object it belongs to, with the metric/field/container written into `Display containers/field anchors`.
- If a pending-adjudication question blocks a metric/field definition, it must state which first-class business object it belongs to, rather than only saying it blocks some field or formula.
- The Agent must first judge the first-class business objects in the source material per the S4 domain model, and must not let pages/APIs/fields usurp that role.
- Placeholder statements are forbidden in the closed-loop area (e.g., "to be added / triggered per source condition / per source action / object pending confirmation")
- Undetermined/pending-confirmation/TBD wording must be written into `## Pending-decision critical issues`, and must not remain in the closed-loop area
- A single rule cluster carries only one business-adjudication question; merging different adjudication questions into the same chain is forbidden
- It is forbidden to split the same business action into multiple chains merely because it appears in different UI containers/API fields; if a split is genuinely required, the difference in adjudication object must be stated.
- High-contribution S3 `propositions` sources (same-source high-value contract/evidence reaching a threshold) must be explicitly cited in the S5 work draft
- If the Agent judges that a source's semantics should not enter the main chain, it must be assignable to pending adjudication, `presentation_context`, implementation support, or noise, with an explanation of why it does not constitute a business adjudication; material affecting business adjudication must not be dropped without explanation.
- If the input-disposition summary declares that a category of material enters the closed-loop or pending-adjudication area, the body text must contain a corresponding closed-loop chain or pending-adjudication question.
- S5 must follow the Markdown skeleton in `distill-authoring-contract.md` when drafting: ordering-rationale headings are neither bold nor code; every closed-loop chain explicitly states `Domain object / State change / Business action / Display containers/field anchors`; every `###` under structured detail must be a table or layered list; every pending-adjudication question must state `Linked chain` or `Linked prerequisite domain` as well as `Decision impact`.
- Script gate: `python3 scripts/distill/s5_work_draft_quality.py --root-id <R>` only validates S5's explicit work-draft contract, including required fields on closed-loop chains, ordering-rationale consistency, pending-adjudication cross-links, placement of undecided terms, and structured-detail shape; it must not generate or replace S5's semantic body text.

S5 merge acceptance (to prevent confusion):

- First form business-adjudication questions from `proposition_items`' `decision_block` / `semantic_roles` / `decision_track`, then write rule chains; the same adjudication question may merge evidence across pages, rather than stitching sentence by sentence.
- A single rule cluster carries only one business-adjudication question (one of visibility/eligibility/issuance/state transition).
- Clauses with different trigger conditions or time windows must be split; forcibly merging on "similar titles" is forbidden.
- Terms must remain unambiguous; if the same word has multiple meanings, define it in the terminology subsection before writing rules.
- Cross-page rule conflicts must be routed to "adjudication/pending"; silently overriding in the body text is forbidden.
- Interface/field information serves only as supporting material and must not usurp and override the business main line.

**Read before drafting**: `distill-quality-bar.md` (**§Objective Function**, §Pre-Draft Triage, §Forbidden), `distill-authoring-contract.md` (**S5/S6 minimal authoring contract**), `distill-document-skeleton.md` (**S4/S5**), `strategy.md` §2.

### S6 · Source brief (Compose ④)

| Output | Rule |
|------|------|
| `_deliver/<slug>/<slug>-source-brief.md` | **Adjudicated reader structure in source language** — same semantics as S5, productized cards; **no translation** |

S6 forbids introducing new business semantics (expression/structure only). Chinese-only narrative rules belong in **S7** when `deliverable_locale` is zh-CN.

S6 mandatory section structure mirrors the locale brief (Overview & scope, Out of scope, Domain model summary, Core business rules, Glossary, Open items, Provenance) — write labels in the **source language**.

**S6 complete (single topic)**: `…-source-brief.md` exists. Then run **S7**.

### S7 · Locale brief (Compose ⑤)

| Output | Rule |
|------|------|
| `_deliver/<slug>/<slug>-domain-brief.md` (English filename shown; actual filename/labels follow `defaults.deliverable_locale` via `deliverable-locale-tokens.json`) | **Target-locale knowledge product**; risk/split **read only this file by default** |

S7 forbids:

- Introducing new business semantics that did not appear in S6 (S7 is **locale expression conversion** only)
- Skipping S6 and drafting only a translated file
- Substituting a template sentence for a condition/consequence
- When locale is zh-CN: substituting English for the target-locale narrative; key business terms use the bilingual term-anchor pattern (`term (English Term)`) on first mention — see `RUNBOOK.zh-CN.md` for the exact zh-CN convention
- Residual process-stage language / internal jargon (`s6-reader-language-policy.json`)

When source language already equals `deliverable_locale`, still emit the canonical S7 filename (content may match S6).

**Evidence insufficiency (mandatory when low/zero tagged sources or `pages_with_props=0`):** place this banner at the top of S7 (locale labels OK):

```markdown
> **Evidence insufficiency** — This module lacks enough tagged Confluence/Jira sources for committed adjudication. Treat as non-SSOT for `@requirement-risk` / `@ticket-splitter` until sources are remounted. See Open items.
```

Prefer reverting Status to **pending** instead of shipping a stub. If the human insists on a placeholder file, the banner + Open items are required.

**Compose complete (single topic)**: **S7 locale brief** exists **without** an insufficiency banner, or with banner explicitly acknowledged as non-SSOT. **Repo-wide gate**: `domain_check.py distill` (**post-S7**).

### S6 · Brief (legacy heading — superseded)

> The long S6 drafting checklist below historically mixed **productization** and **zh-CN conversion**. Prefer the split above: run **S6** in source language, then apply Chinese/locale rules under **S7**. The detailed card/section requirements still apply to **both** S6 (source labels) and S7 (locale labels).

| Output | Rule |
|------|------|
| `_deliver/<slug>/<slug>-domain-brief.md` (English filename shown; zh-CN filename/labels come from `deliverable-locale-tokens.json`) | **S7 locale brief** when `deliverable_locale=zh-CN`; risk/split **read only this file by default** |

S6 forbids:

- Substituting a template sentence for a condition (e.g., "takes effect when entering the business scenario and the prerequisite is met")
- Substituting a template sentence for a consequence (e.g., "affects page display or process branching, subject to implementation")
- Using "to be confirmed with future implementation" to cover a rule clause that should be made explicit in this draft
- Introducing new business semantics in S6 that did not appear in S4/S5 (S6 only allows reader-facing expression conversion)
- Generating reader sentences via template stitching (e.g., repeating "user-visible user-visible," or an obviously truncated "when...")
- Upgrading S5's boundary candidates, noise, engineering collaboration, or release-support material into core business rules
- Writing beta builds, bug lists, sprint/retro, commit frequency, three-party collaboration, project dates, or phase-acceptance cadence into `## Core business rules`; such content may only appear as "not covered in this document," a pending-confirmation item, or a provenance boundary — unless S5 has proven it directly changes a user-visible business commitment
- Substituting English for the target-locale narrative; key business terms must use the locale term as primary, with the bilingual term-anchor pattern on first mention to preserve the original source name; necessary English that is not a source link/path must serve as a field/API/system-name anchor or be explained in `## Terminology`
- Residual process-stage language, internal-acceptance jargon, or legacy internal slang; the general list of forbidden expressions is configured in `domain-knowledge/language/s6-reader-language-policy.json`, and the script only reads that policy and reports hit categories — it does not encode business-domain rules
- Compressing a source mapping table, state enum, field list, formula/threshold table, time-window table, or visible-copy list into an unqueryable summary; if such detail affects the reader's ability to judge the rule path, it must be preserved as a queryable structure or moved into pending-confirmation items

S6 core-rule expression requirements:

- Express rules in reader-facing natural language; do not fall back on a fixed field template.
- Every core-rule subsection must be a reader decision card, stably containing `Confirmed rule`, `Open boundary`, `User-visible effect`, and `Linked open items`; each label must be its own bold list item, with concrete conditions, branches, time windows, exceptions, visible consequences, and source semantics placed in indented sub-items. These are productized reading structures, not the old rule-cluster field template.
- A top-level bullet under `Confirmed rule` carries only one reader judgment point; semicolons must not be used to compress multiple branches, phases, targets, rewards, or display consequences into one item. When enumeration is needed, write a summary first, then express detail via indented sub-items or `## Key details`.
- The main text must be primarily written in the target locale; for any key business term declared with the bilingual term-anchor pattern in `## Terminology`, if the body uses that locale term, its first occurrence in the body must be written the same way, with the anchor; subsequent occurrences may use the locale term only.
- Necessary English is retained only as the bracketed original source name, a field/API/system name, a business-specific abbreviation, or a source link/path.
- Field/API/system names must be anchored with backticks; business-specific abbreviations must be explained in `## Terminology`.
- Every core rule must be traceable to an S5 closed-loop chain or pending-adjudication question.
- Every core rule must retain the conditions, branches, time windows, exceptions, user-visible impact, and source semantics supported by S5.
- Metrics, fields, and display containers serve only as anchors that explain a rule; they must not usurp it.
- When a rule depends on structured detail, the reader decision card should state only the decision meaning; queryable detail goes into `## Key details`, or into a `Detail` sub-block under the same card. Do not substitute "see source for details" for the detail, and do not scatter detail across long sentences.
- S6 must follow the Markdown skeleton in `distill-authoring-contract.md` when drafting: the domain-model summary uses layered labels; every decision card uses independent bold labels and indented sub-items; every `###` under `## Key details` must be a table or layered list; every action item under `## Pending confirmations` must have `Affected rule` as the primary item, with `To confirm/supplement`, `Suggested reviewer`, and `Post-confirmation impact` as indented sub-items.

S6 mandatory section structure:

- `## Overview & scope`: states the subjects, business scope, and external-reader perspective covered by this topic
- `## Out of scope`: lists engineering implementation, noise, boundary candidates, or topics pending migration
- `## Out of scope`: must carry the demotion note for delivery/collaboration/acceptance-cadence material; such content must not drift into the core rules
- `## Domain model summary`: carries only S5's first-class business objects, object relationships, and state machines — no re-modeling; first-class business objects, object relationships, and state machines/state transitions must be expressed with bold labels plus indented sub-items, avoiding compressing multiple objects or states into one long list item
- `## Core business rules`: writes reader decision cards in S5's ordering; every card must use independent bold labels to distinguish the confirmed rule, the boundary pending confirmation, the user-visible impact, and the associated pending-confirmation item, with the specifics written into indented sub-items
- `## Key details` (conditional): must appear whenever S1/S5 contains a mapping table, state enum, field list, formula/threshold table, time-window table, or visible-copy list; split into `###` subsections by business rule, each preserving queryable detail via a table or indented list. If the source cannot form stable detail, `## Pending confirmations` must state what is missing and its impact once supplied.
- `## Terminology`: only explains terms already used in S5/S6, adding no new rules; key business terms use the bilingual term-anchor pattern, and this section also serves as the checklist for the body's first-mention anchor check; any business English abbreviation or proper English name retained in the S6 main text must be explained here
- `## Pending confirmations`: categorized by `Domain boundary / Rule conflicts / Data & interface / Policy & presentation / Materials to supplement`; every pending-confirmation item must be written as an action item, with `Affected rule` as the primary list item, and `To confirm/supplement`, `Suggested reviewer`, `Post-confirmation impact` as indented sub-items
- `## Provenance`: lists the work draft, aggregate index, proposition list, proposition JSON, and materialized directory
- If placeholder clusters exist: they must appear under the `Materials to supplement` category of `## Pending confirmations`

S6 production method (first principles, not template fill-in):

- First carry forward the **S5 layered model summary**: first-class business objects, object relationships, and state machines undergo expression conversion only
- Then write **business-reader-readable rule chains**: every rule retains its conditions, branches, time windows, exceptions, and user-visible impact
- Then perform **structured-detail fidelity**: whenever the source already has a queryable table, enum, field mapping, threshold, or time window, do not compress it away inside a rule card; preserve it as a reader-searchable `## Key details`
- Then produce a **pending-question index**: domain boundary, rule conflict, data & interfaces, policy & display, material to be supplemented; every pending-confirmation item must be actionable
- Finally write **provenance**: engineering noise is forbidden from entering the core-business-rule main line
- **Mandatory human-judgment point**: threshold-rule conflicts, time-window conflicts, and state-transition conflicts must be human-confirmed before the brief can be issued

Based on the **S5 work draft**; you may reference the previous round's [`glossary.md`](../../../domain-knowledge/language/glossary.md) to keep reader language consistent. New terms from this round are folded back into the glossary after S6.

S6 generation principles (main path):

- S6 is the reader-facing knowledge-productization expression-conversion layer over S5, not a semantic-recreation layer.
- S6 may optimize readability and terminology consistency, but must not add or remove business-adjudication semantics.
- Semantic revisions must go back to S4/S5 to be completed; S6 only carries forward already-confirmed semantics.

**Compose complete (single topic)**: **S7 locale brief** exists (after S6 source brief). **Repo-wide gate**: `domain_check.py distill` (**post-S7**).

---

## User Phrasing

| Intent | Phrasing |
|------|------|
| Sync + Recognize | `@generate-knowledge-from-wiki <url>` (stops after **S2** by default) |
| Run Compose | **`continue`** or `@distill-domain-knowledge <R>` |
| A sub-step for one topic | `… topic checkout S3` / `S4` / `S5` |

---

## Reporting Template

- **Ingest (S1)**: page count, landing root
- **Recognize / Prep (S2)**: domain blocks; closure; confirmation-page **confirmed / pending** row counts
- **Compose (S3–S6)**: for each **confirmed** topic: aggregate / domain model / work draft / brief — **present/absent**
- **Forbidden**: reporting "brief complete" when only S3/S4/S5 exist

---

## Appendix · Step Quick Reference

### Three Stages ↔ S1–S6

| Stage | Step | Goal | Human |
|------|-----|------|------|
| **Ingest** | **S1** | Confluence → `materialized/` (coarse machine triage) | none |
| **Recognize** | **S2** | Confirmation page + closure (proposition-level) | **stop**: mark **confirm** |
| **Compose** | **S3** | `_aggregate/` (confirmed rows only) | none |
| **Compose** | **S4 / S5 / S6** | Domain model → work draft → brief | optional acceptance |

### Prep / Compose (aliases)

| Segment | Step | Goal | Human |
|----|-----|------|------|
| **Prep** | **S1 + S2** | Ingest + Recognize | **stop**: mark **confirm** |
| **Compose** | **S3 → S6** | Compose | none (or optional acceptance) |

### Step ↔ Docs and Gates

| Step | Agent must read | Main writes | Gate |
|----|------------|----------|------|
| S1 | `SKILL` → `S1-SYNC-CLI.md` | `extracted/`, `materialized/`, `PIPELINE_HANDOFF.json` | script exit code |
| S2 | this RUNBOOK · `strategy.md` §2 | `DOMAIN_MODULE_CHECKLIST.md`, `_materialization_closure.json`, `S2_DECISION_LEDGER.json`, `S2_REVIEW_DECISIONS.json` | `python3 scripts/distill/coverage.py --root-id <R>` |
| S3 | this RUNBOOK | `_aggregate/<slug>/` | coverage (recommended) |
| S3.5 | this RUNBOOK | `_aggregate/<slug>/*-propositions.json`, `*-propositions.md` | `python3 scripts/distill/proposition_quality.py --root-id <R>` |
| S3.6 | this RUNBOOK | `_aggregate/<slug>/*-decision-atoms.json\|md`, `*-conflict-ledger.md` | `python3 scripts/distill/decision_atom_quality.py --root-id <R>` + `python3 scripts/distill/conflict_ledger_quality.py --root-id <R>` |
| S4 | `distill-quality-bar.md` §Objective Function · `distill-document-skeleton.md` | `_deliver/*-work-draft.md` (Agent-authored) | `quality.py` (validates against Skill MUST) + `domain_layout.py` |
| S6 | previous round's `glossary.md` (optional reference) + this round's terminology notes | `_deliver/*-domain-brief.md` (Agent-authored; filename per `deliverable-locale-tokens.json`); `glossary.md` auto-updates after S6 | `python3 scripts/run_distill_gate.py --root-id <R>` (includes `domain_check distill` + `glossary_update.py`) |

**Language**: S1–S6 = source language; **only S7** = `deliverable_locale` (zh-CN / en).

### Gate Layering and Failure Attribution (S2/S3/S4/S5/S6)

| Layer | Representative gate | Primary failure attribution | Handling principle |
|---|---|---|---|
| S2 recognition layer | `coverage.py` | Script execution layer (recognition/closure/blocking) | Fix recognition and mapping rules first, then proceed to S3 |
| S3 structure layer | `proposition_quality.py`, `s3_quality.py`, `decision_atom_quality.py`, `conflict_ledger_quality.py` | Script execution layer (extraction/normalization/indexing) | Fix extraction and normalization first; do not patch it in S4/S5/S6 |
| S4 model layer | Work-draft `## Domain model` acceptance | Skill/Agent contract layer (domain-object and state modeling) | Go back to the domain model; do not stack rule chains to mask a missing model |
| S5 semantic layer | Work-draft human acceptance (model attachment, rule-chain density, explicit conflicts) | Skill/Agent contract layer (re-attachment and adjudication) | Go back to semantic re-attachment; do not loosen gate thresholds to mask the problem |
| S6 commitment layer | `s6_reader_quality.py` | Mixed attribution: boundary overreach → Skill; missing reader structure → Script | S6 performs reader-facing expression conversion; semantic defects fall back to S4/S5 for repair |

Quick triage:
- **Missing structure / missing field / broken index**: default to a Script-layer issue.
- **Unadjudicated conflict / merged rules / commitment overreach**: default to a Skill/Agent-layer issue.
- **Misjudged intent triage**: first tighten the trigger condition at the Script layer (high-confidence trigger); loosening the overall threshold to mask it is forbidden.

### Re-runs

| Scenario | Entry point |
|------|------|
| Skip sync | [`distill-domain-knowledge`](../distill-domain-knowledge/SKILL.md) |
| Finished marking **confirm** | **`continue`** (S3→S7) |

Staged re-run (script):
- `python3 scripts/distill/compose_rerun.py --root-id <R> --stage s3_build`
- `python3 scripts/distill/compose_rerun.py --root-id <R> --stage s4_work_draft` (only checks that `_deliver/*-work-draft.md` already exists and is not older than S3)
- `python3 scripts/distill/compose_rerun.py --root-id <R> --stage s6_final_draft` (only checks that `_deliver/*-domain-brief.md` already exists)

## Next

`@requirement-risk` → `@ticket-splitter` (evidence: `_deliver/<slug>/<slug>-domain-brief.md`).
