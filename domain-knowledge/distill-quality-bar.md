# Distill Quality Bar (Repository-Wide)

Chinese locale: [`distill-quality-bar.zh-CN.md`](./distill-quality-bar.zh-CN.md).  
Deliverable label map (en ↔ zh-CN): [`language/deliverable-locale-tokens.json`](language/deliverable-locale-tokens.json).  
Agents emit labels for `defaults.deliverable_locale` from that map; this English doc cites **English** labels only.

After the orchestration script completes **S1**, Cursor writes **`curated/`** (**S2–S7**) following **[`generate-knowledge-from-wiki/RUNBOOK.md`](../.cursor/skills/generate-knowledge-from-wiki/RUNBOOK.md)**:

| Phase | Step | Meaning | Language |
|----|-----|------|------|
| **Prep** | **S1** | (script) `extracted/`, `materialized/` | Source |
| **Prep** | **S2** | `DOMAIN_MODULE_CHECKLIST.md` (domain module confirmation page) + full-file tagging + `_materialization_closure.json` | No rewrite |
| **Compose** | **S3** | **`confirmed` rows only**: `_aggregate/<slug>/` | Source |
| **Compose** | **S4** | `## Domain model` in `_deliver/…-work-draft.md` | Source |
| **Compose** | **S5** | Model-mounted rule chains in `_deliver/…-work-draft.md` | Source |
| **Compose** | **S6** | `_deliver/…-source-brief.md` | **Source language (no translation)** |
| **Compose** | **S7** | `…-domain-brief.md` | **`deliverable_locale`** |

**`confirmed`** (confirmation-page status) = approving the **domain-block partition** and authorising **Compose**; it does **not** mean the locale brief is complete.

- **[`domain-knowledge/strategy.md`](strategy.md)** — knowledge focus, language, layout, business rules must be written in full
- **[`generate-knowledge-from-wiki/RUNBOOK.md`](../.cursor/skills/generate-knowledge-from-wiki/RUNBOOK.md)** — S2 domain recognition · S3–S7 Compose; for supplemental runs see [`distill-domain-knowledge/SKILL.md`](../.cursor/skills/distill-domain-knowledge/SKILL.md)

This document lists only **enforceable, cross-domain baselines**. Where it conflicts with a Skill, the Skill + strategy take precedence.

---

## Three-Layer Baseline (Artifacts · Done · Rhythm)

The three sentences below are the governing standard for this entire document; procedural detail lives in the Skill and is not expanded here.

1. **Artifacts**: `materialized/` = synced source material; `_aggregate/` = per-block aggregation (not an external commitment); `…-work-draft.md` = S4 domain model + S5 model-mounted rule chains (not a locale-language commitment); `…-source-brief.md` = S6 source-language authoritative brief; `…-domain-brief.md` = **S7** target-locale domain commitment.
2. **Done (finalised)**: only when **S7** is complete — same-topic rules merged into a single statement per condition, conflicts **explicitly marked for review**, **traceable** (Confluence link + one `materialized/` path in the provenance section); and the corresponding **S6** source-language brief must already exist.
3. **Rhythm**: `@generate-knowledge-from-wiki` defaults to completing **Prep (S2)** then **pausing**; after a human sets status to **`confirmed`** the agent **continues** Compose (S3→S7, batchable by slug). **Forbidden** to report "locale brief finalised" when only `_aggregate/`, a domain model, a work draft, or an S6 brief exists.

## Responsibility Assignment (Quality-Judge Perspective)

- **Skill/Agent owns**: defining each step's goals and forbidden items, the domain model, conflict-resolution rules, and the S6/S7 commitment structure.
- **Script owns**: extraction / normalisation / graph construction and gate checks, failure lists and traceable evidence.
- **Script forbidden items**: must not generate S4/S5/S6 body-text fallback templates; must not reverse-engineer the S3 semantic layer from S6.
- **Failure attribution**:
  - Missing artifact / incomplete fields / gate failure → first attribute to `Script execution layer`.
  - Unresolved rule conflict / semantic conflation / commitment boundary overrun → attribute to `Skill/Agent contract layer`.

### Deprecated Path Declaration

- The `S6 → decision_atoms → S5/S4` reverse-flow path is deprecated and is no longer accepted as a historical-compatibility interpretation.
- Any template main-path of the form `WORK_DRAFTS` / `FINAL_DRAFTS` is treated as a non-compliant implementation.

---

## Objective Function (Priority Order)

Aligned with [`strategy.md`](strategy.md) §1 "Compose priority order"; **this section is the execution judge for S4–S6** (priority order, anti-goals, and details expanded below).

1. **Domain modelling**: first establish first-class business objects, metrics/fields, display containers, object relationships, state machines/state transitions, and boundary candidates in a layered structure, then mount the rule chains; the **wrong** goal is to pile up rule lists directly, treat metrics/fields/pages as objects, or retain the Confluence section appearance.
2. **Semantic re-mounting**: organise by domain propositions (eligibility—branch—consequence, visible scope, time window); the **wrong** goal is "delete as few characters as possible, preserve Confluence section order and heading appearance."
3. **Business noise isolation**: collaboration schedules, pure ticket matrices, email walls, DDL/SQL/Git, mechanical field dumps with no business explanation → **divert from the main decision chain as supporting material/noise; do not let them masquerade as business rules**.
4. **Completeness (business side)**: every clause affecting "whether a user/consultant will experience a visible consequence" must be **written in full and verifiable**; merge duplicates; do **not** substitute "see `materialized/`" for a complete rule chain.
5. **Language**: **S1–S6: no translation**; S6 produces the source-language brief (`*-source-brief.md`); **S7** produces the locale brief (`*-domain-brief.md`) in `deliverable_locale`.

### Readability First (Final Deliverable)

- The S7 main text must follow "business narrative first": give the business reader scope, a model summary, and readable rules before pending classifications and provenance.
- Decision Atom / Conflict Ledger is a machine-and-review layer; it does not replace the main-text reading experience.
- Forbidden to flatten atomic fields directly into the body text, producing a result that is "verifiable but unreadable."
- The S7 `## Domain model summary` must be layered: first-class business objects, object relationships, and state machines/state transitions expressed with bold labels and indented sub-items; avoid crowding multiple objects or states onto the same line.
- Each core rule in S7 must be a reader decision card, reliably containing `Confirmed rule` / `Open boundary` / `User-visible effect` / `Linked open items`; each label must be a standalone bold list item with specific content in indented sub-items; readers must not be forced to reconstruct rule boundaries from prose or long sentences.
- The `Confirmed rule` in S7 must not compress multiple branches, phases, goals, rewards, or display consequences into a single top-level bullet with semicolons; any content a reader needs to judge by branch must be broken into layered sub-items or placed in a queryable structure under `## Key details`.
- The `## Pending confirmations` in S7 must be an action index, not a note list; each pending-confirmation item must use `Affected rule` as the primary list item, with `To confirm/supplement` / `Suggested reviewer` / `Post-confirmation impact` as indented sub-items.
- S7 must contain: `## Overview & scope` / `## Out of scope` / `## Domain model summary` / `## Core business rules` / `## Terminology` / `## Pending confirmations` / `## Provenance`.
- S7 must not promote S5 boundary candidates, noise, engineering collaboration, or release/compliance support into core business rules.
- S7 must not promote beta/experience versions, bug lists, sprint/retro notes, code commit frequency, third-party collaboration, project start/end dates, or phase acceptance rhythm into core business rules; this material may only appear as delivery boundaries, pending confirmations, or provenance evidence. If it genuinely affects user-visible quality, it must be rewritten as "which business object's visible outcome is affected," not preserved as a delivery-process narrative.
- S7 must not contain `$1`, `TODO`, obviously truncated acceptance sentences, or repeated template artefacts.
- S7 main text uses `deliverable_locale` as its primary language. For bilingual terms declared in `## Terminology`, the first occurrence in the main text must use the same bilingual anchor; subsequent occurrences may use the locale term only. Necessary English is allowed only as: source-name in parentheses, field/API/system name in backticks, a business-specific abbreviation explained in `## Terminology`, or a source link/path in `## Provenance`. Field/API/system names must use backticks as anchors; business abbreviations must be explained in `## Terminology`.
- S7 reader-language refinement is governed by `domain-knowledge/language/s6-reader-language-policy.json`; scripts perform deterministic checks only and must not encode domain-specific business knowledge in language gates.
- S7 must preserve structured business detail from sources: mapping tables, state enumerations, field lists, formula/threshold tables, time-window tables, and visible copy lists must not be swallowed by summaries. If these details affect rule paths or user-visible judgements, S7 should add `## Key details`, organised in `###` subsections by business rule, preserving queryable tables or indented lists; if sources are insufficient to form stable detail, this must be noted in `## Pending confirmations` with the content to be supplemented and the post-completion impact.

### Merge Quality Baseline (Clear, Reasoned, Unambiguous)

- A single rule cluster carries only one business decision question; different decision questions must be split.
- Merging is allowed only when "subject + trigger condition + time window + visible consequence" share the same source; if any key axis differs, split.
- Conflicting scopes must not be silently absorbed: "adopted rule" or "pending confirmation" must be written explicitly.
- After merging, the body should maintain "rule main line first, implementation support after," avoiding interface fields dominating over business semantics.
- Named business structures are first-class semantic objects: named branches, phases, paths, tiers, levels, statuses, cycles, markets, cards, etc. in source material that carry business-decision or user-visible-impact meaning must have their business meaning preserved in S4/S5 — written into the domain model, main chain, or pending-decision area.
- Forbidden to abstract named business structures into anonymous conditions until they disappear; normalised naming is acceptable, but the name a reader needs to judge the rule path must not be lost.
- Forbidden to rewrite queryable structured detail as generalisations like "several fields," "multiple statuses," "related mappings"; S7 may use product-friendly language but must not sacrifice a business reader's ability to look up answers by number, status, field, or time window.
- S3 must tag tabular-source signals: when S1 contains long mapping tables, field tables, state enumeration tables, eligibility/level/reward tier tables, time-window tables, or visible-copy tables, the S3 page-level `structured_source` must record the structural signal, header/fields, dense-row count, and sample rows; this is script-side structural fidelity, not a business decision.
- S5 must accept structured-detail handoff: when an S3 proposition, S3 page-level `structured_source`, or S5 semantic re-mounting discovers mapping tables, state enumerations, field lists, formula/threshold tables, time-window tables, visible-copy lists, or numbered/tier/level mappings, the work draft must write `## Structured detail handoff`. S5 must first adjudicate granularity as "full expansion / rule-compressed / pending confirmation," then preserve queryable tables or layered lists per business-rule subsection. `## Key details` in S7 may only come from this section; skipping back to S1 to supplement detail is forbidden.
- S5 structured-detail three-way granularity decision is the acceptance standard: when readers need to query or judge each item individually and each row may change an identity/eligibility/reward/status/field/time-window/copy/exception, it must be **fully expanded**; when sources can be losslessly generated by a stable formula, continuous numbering, arithmetic threshold, or isomorphic naming with no independent exception meaning per row, **rule-compressed** form is allowed — and must include range, formula/step, endpoints, exceptions, and an example; when sources conflict, are incomplete, have unclosed field meaning, unconfirmed user visibility, or unstable display position, the item must be listed as **pending confirmation** and must not use a complete table to fabricate false certainty.
- Excluded material, engineering collaboration, release/compliance support, pending-migration topics, and unattributed material are not domain objects; they must not appear under domain objects in `## Domain model`; they may only appear as input disposition, boundary pending-decision, or exclusion notes.
- Delivery-collaboration material is not a domain object: beta/experience versions, bug lists, sprint/retro notes, code commit frequency, third-party collaboration, project dates, and phase acceptance milestones must not appear as first-class business objects or core rules; they may only be demoted to display-quality support, delivery boundaries, or pending confirmations.
- Semi-closed chains and pending-decision problems must be bidirectionally linked consistently: when a chain references "Issue N," "Issue N" must exist and back-reference that chain; the pending-decision problem must also state `Decision impact`.
- `## Ordering rationale` is the sole truth for chain ordering; other subsections may only summarise the ordering normalisation principle and must not define a separate detailed chain order.
- `## Domain model` must be layered: first-class business objects, metrics/fields, display containers, object relationships, state machines/state transitions, and boundary candidates each in their own section; metrics, progress indicators, formulas, amount fields, API tokens, and page cards must not mix into first-class business objects.
- Closed-loop chains must attach to the layered model: the domain object within a chain must come from first-class business objects; metrics, fields, formulas, amounts, progress indicators, goals, pages, cards, lists, and APIs may only enter display containers/field anchors and must not serve as chain domain objects.
- S4 model gate is enforced by `scripts/distill/domain_model_quality.py`: validates only the layered model, chain-object inheritance, and field/API/page demotion; does not generate S4/S5 body text.
- S5 work-draft gate is enforced by `scripts/distill/s5_work_draft_quality.py`: validates only closed-chain fields, organisational order, pending-decision cross-links, unresolved-word placement, and structured-detail form; does not generate S5 body text.

### Default: Write Full Rule Chains Whenever Source Supports Them

- **Whenever** source material can be organised into a **business rule chain** under the **`strategy.md` industry template** (subject / condition / branch / time window / visible consequence, with traceability), **this path's curated document should write that chain in full** and **not** use a Pass placeholder for convenience.
- **`facet-unmatched/`** is merely a script-side materialisation folder name and does **not** mean "blanket Pass is allowed"; every page still requires individual judgement about whether a business chain exists.
- **S2** tags domain recognition; **S3** aggregates confirmed-block pages only; **S4–S6** proceeds by topic in batches. Use **Pass** **only** when the whole page is clearly non-business (see below); do **not** use Pass to avoid writing the model and rule chains that S4/S5 can produce.

---

## Pre-Authoring Triage (Mandatory)

Classify source material into three types before writing:

| Type | Treatment |
|----|----------|
| **Specification layer** | Member/consultant-visible consequences, thresholds, branches, copy scope → **business rules** and equivalent semantic sections, written as distinct points. |
| **Mapping & presentation** | Gateway/Path/fields, UI data rules → **data & interface / presentation notes**, structured lists preferred; avoid large tables. |
| **Collaboration & ops noise** | Does not occupy the main body. |

S3 fidelity-triage contract (script hard constraint):

- Page level must be tagged with `doc_intent`: `rule_spec` / `api_contract` / `release_change` / `test_ops` / `discussion_decision`.
- Page level must be tagged with `structured_source`: even when individual propositions from long tables/mappings/enumerations/field lists are weak, the structural signal and sample rows must be preserved for S5 to judge whether `## Structured detail handoff` is needed.
- Proposition level must be tagged with `candidate_type`:
  - `contract_candidate`: enters the `decision-atoms` minimal audit view; S4/S5 Agent is still responsible for the domain model and semantic re-mounting.
  - `evidence_note`: preserves evidence and semantic anchors for S4/S5 delayed adjudication; does not enter the decision main chain directly.
  - `noise_context`: isolates noise with no business-decision value; does not enter the S4/S5 main chain by default.
- Each proposition must include `eligibility_reason` and preserve `scope/evidence_span` provenance anchors.
- Each proposition must include `semantic_roles` / `semantic_preservation_reason` / `business_scope_label` to prove S3 has not silently dropped semantics.
- Each proposition must include `decision_track` (`decision_core` / `presentation_context` / `unresolved_critical` / `noise_context`) and `causality_score`.
- Only `decision_core` may serve as S5 main-decision-chain input; `unresolved_critical` must explicitly enter "pending-decision critical issues"; `presentation_context` provides only presentation/background evidence.
- S3 is forbidden from inferring business branches based on a single sample, threshold magnitude, or local keyword; only the source material's explicit structure is preserved — domain model and branch meaning are re-mounted by the S4/S5 Agent.

High-confidence trigger principle (gate policy):

- For `doc_intent`-related "proportion" gates, use high-confidence triggering (strong title match + sample-size threshold) before hard-failing.
- Forbidden to amplify heuristic intent-recognition errors into full-pipeline failures.
- Forbidden to mask triage problems by lowering the overall threshold; fix classification trigger conditions and candidate eligibility rules first.

Causal closure priority principle:

- Quality evaluation focuses first on whether "condition → branch → consequence" is closed, not merely on field fill rate.
- High-signal propositions containing unresolved/pending/TBD markers must enter `unresolved_critical`; silently merging them into presentation context is forbidden.
- `presentation_context` may be retained but must not crowd out the decision main-chain proportion.
- Single-stage admission must be auditable: each proposition must carry `admission_stage1_result`; `noise_context` must have `admission_drop_reason`.
- Anti-false-kill gate: if a large number of high-causality propositions (`decision_core/unresolved_critical` with `causality_score` meeting the threshold) are not entering the contract, S3.5 must hard-fail.

---

## S2–S7 and `confirmed` Status — aligned with RUNBOOK

- **S2**: domain module confirmation page + **full-file tagging** + `_materialization_closure.json`; when multiple topics reference the same source → **index only; pasting source text into multiple directories is forbidden**.
- **S3** (**`confirmed` rows only**): `_aggregate/<slug>/` aggregation; **no** translation requirement, **no** narrative-final requirement.
- **S4**: `## Domain model` in `_deliver/<slug>/<slug>-work-draft.md` — domain objects, states/phases, business actions, state changes, display containers/field anchors; **language unchanged**.
- **S5**: `_deliver/<slug>/<slug>-work-draft.md` — rule chains mounted on the S4 model, semantic re-mounting, full business write-up; **language unchanged**.
- **S6** (same topic): `_deliver/<slug>/<slug>-source-brief.md` — source language, no translation; internal reference.
- **S7** (same topic): `_deliver/<slug>/<slug>-domain-brief.md` — `deliverable_locale`; **the default external-facing read target**.
- **How to cite drafts / synced material**: **only** in **`## Provenance`** (or an equivalent subsection), retain **one** of the minimal forms:
  - Authoritative page: **Confluence link** (primary provenance);
  - Machine materialisation layer (optional **one line**): `domain-knowledge/materialized/by-root/<root>/<relative-path>.md` or a single in-repo path as plain text; **do not** expand `materialized/` content in the body.
- **Same-layer cross-reference**: citing another final brief within `curated/` using a short cross-reference or "see the sibling doc" is acceptable; do **not** confuse this with "citing a draft."

**Gate script**: `scripts/distill/quality.py` detection against `domain-knowledge/materialized/` applies **only to the body before the first `## Provenance` heading**; one draft-path line is allowed inside the provenance section (consistent with "forbidden to link back to `materialized/` in the body").

## Forbidden Patterns (Anti-Patterns)

- **Forbidden** to use a chain of **`### [Confluence section title](url)`** as the main body directory (treating source structure as domain structure).
- **Forbidden in the main body** (`## Overview` … `## Pending` and equivalent sections) to **link back** to **`domain-knowledge/materialized/`** or paste synced-draft source text in place of a curated brief; **`materialized/` is only allowed as a one-line path under `## Provenance`** (see above). **S7 locale briefs** must also remove "skeleton/to-be-filled" meta-language.
- **Forbidden** when a `materialized/` path exists not to write the corresponding `curated/` file (even a Pass must have a landing).
- **Forbidden** to conclude that "a module is covered" based solely on **file-name pattern** or **`facet-*` directory name** — **S2** must combine the **`strategy.md` proposition yardstick** and **`materialized/` full-text search** to complete the closure/checklist path; a previously stable `glossary.md` may only serve as a synonym/abbreviation hint, not as a domain-boundary basis; **S4–S5** then build the model and merge the body. This is especially important when the same business concept is scattered across multiple pages.
- **Forbidden** to substitute template sentences for rule chains (e.g. "takes effect upon entering the business scenario," "subject to subsequent implementation"); these sentences provide no actionable decision information.
- **Forbidden** to have "condition/consequence" labels with no specific anchors (thresholds, state transitions, time windows, API/field tokens, enumeration values).
- **Forbidden** to omit S7 mandatory fields: `applicable subject / handling branch / time window / exception / reference source` (absence = not finalised).
- **Forbidden** to merge clauses with "different time windows / different eligibility scopes" into the same rule cluster, misleading readers.
- **Forbidden** to use multiple undeclared meanings for the same term within a single document.

---

## Pass (Clearly Non-Business) — Narrow Definition

Use Pass **only** when the **entire page** is pure collaboration/ops/engineering process **and** contains no material that can be organised into a business rule chain.  
A minimal file must still be written at the **same path**: **`## Non-business determination (Cursor)`** + **`## Provenance`**; **forbidden** to leave a blank file; **forbidden** to use Pass to **avoid** rule chains that could be written.

---

## Recommended Section Skeleton (Domain-First · Script-Verified)

- For curated documents mixing **business + interface**: follow **[`distill-document-skeleton.md`](distill-document-skeleton.md)** (narrative first half, implementation support second half).
- **Scripts do not write body semantics**; after writing to disk, use **`scripts/distill/domain_layout.py`** to verify that "business sections precede implementation sections," avoiding another purely interface-spec output.

## Script Self-Checks (Non-LLM)

Run after sync or distill iterations:

```bash
# Provenance closure: every materialized/*.md has a landing in curated —
# priority: _materialization_closure.json (domain reorganisation),
# else default same-name relative path (backward-compat); use --exclude-prefix to suppress some prefixes
python3 scripts/distill/coverage.py --root-id <root-page-id>

# Proposition layer: confirmed topics must have per-page proposition lists (S3.5)
python3 scripts/distill/proposition_extract.py --root-id <root-page-id>
python3 scripts/distill/proposition_quality.py --root-id <root-page-id>

# Semantic layer: Decision Atom + Conflict Ledger (S3.6)
python3 scripts/distill/decision_atom_sync.py --root-id <root-page-id>
python3 scripts/distill/conflict_ledger_sync.py --root-id <root-page-id>
python3 scripts/distill/decision_atom_quality.py --root-id <root-page-id>
python3 scripts/distill/conflict_ledger_quality.py --root-id <root-page-id>

# Heuristic: mirrored skeleton / body links back to materialized, etc.
# (Pass drafts automatically skip deep rules)
python3 scripts/distill/domain_model_quality.py --root-id <root-page-id>
python3 scripts/distill/s5_work_draft_quality.py --root-id <root-page-id>
python3 scripts/distill/quality.py --root-id <root-page-id>

# Domain-first layout: business sections must precede "implementation/interface" major sections
# (Pass and small files may skip)
python3 scripts/distill/domain_layout.py --root-id <root-page-id>
```

---

## Relationship to `PIPELINE_HANDOFF.json`

`scripts/sync_domain_knowledge_from_confluence.py` writes **`distill_quality_bar_doc`** into **`domain-knowledge/extracted/by-root/<root-page-id>/PIPELINE_HANDOFF.json`**, pointing to this file, so the Agent can load the same requirements immediately at the start of **Recognize / Compose (S2+)**.
