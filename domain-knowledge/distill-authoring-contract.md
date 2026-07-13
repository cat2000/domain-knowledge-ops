# S5–S7 Authoring Contract

Chinese locale: [`distill-authoring-contract.zh-CN.md`](./distill-authoring-contract.zh-CN.md).  
Deliverable label map (en ↔ zh-CN): [`language/deliverable-locale-tokens.json`](language/deliverable-locale-tokens.json).  
Agents emit labels for `defaults.deliverable_locale` from that map; this English doc cites **English** labels only.

This contract defines the minimum required output form for the Compose phase covering S5, S6, and S7. It is a cross-domain constraint: the Agent is responsible for business-semantic judgements; scripts only verify that those judgements are expressed explicitly in a stable, reviewable Markdown structure.

## Why This Contract Exists

Quality failures in S4/S5/S6/S7 are usually not caused by missing S1/S3 evidence, but by scattered generation constraints that leave the Agent understanding the principles without producing output in the fixed form the gates require. The root-cause fix is to explain the required author interface in one place:

- S5 must explicitly express model mounting, business ordering, pending-decision cross-links, and structured detail.
- S6 converts the S5 work draft into a source-language brief (`*-source-brief.md`) without translation; it must not add or drop business semantics.
- S7 converts the **S6** source brief into a reader-facing knowledge product in `deliverable_locale`; it must not add or drop business semantics.
- Domain-specific content goes into the generated body only, not into this contract.

## S5 Work Draft: Section Order

Every `*-work-draft.md` must use the following top-level order:

1. `## Overview & scope`
2. `## Input disposition summary`
3. `## Domain model`
4. `## Ordering rationale`
5. `## Closed-loop decision chains`
6. `## Pending-decision critical issues`
7. `## Structured detail handoff` — when S3/S5 contains queryable structured detail
8. `## Provenance`

`## Overview & scope` is mandatory even for work drafts, because S5 is already a domain-knowledge work draft, not a raw implementation ledger.

`## Provenance` must list Confluence URLs or equivalent source links for S3's high-contribution, high-value sources; only source titles or semantic evidence appear in the body — source links are concentrated in the provenance section.

## S5 Input Disposition Summary

`## Input disposition summary` must explicitly mention and dispose of the three categories of S3 input:

- `contract_candidate`:
  - State whether it enters a closed-loop chain, is split into a semi-closed chain, enters pending-decision, or is excluded, and why.
- `evidence_note`:
  - State whether high-value evidence is promoted to a closed-loop chain, split into pending-decision, retained as structured detail, or excluded for a stated reason.
- `noise_context`:
  - State whether it is excluded, demoted to a boundary/support evidence, or recorded as a pending-confirmation boundary.

Also must address:

- Semantic normalisation: how repeated signals, cross-page signals, cross-UI signals, and cross-API signals are merged, demoted to field anchors, or split.
- Source/order normalisation: whether source order represents business order; if not, how it is converted to business-decision order.
- Cross-topic handoff: if `_aggregate/CROSS_SLUG_HANDOFF.md` contains pages pointing to the current slug, state that the page has been absorbed, demoted to field/display/boundary evidence, or excluded for a stated reason; silently ignoring it because the source directory belongs to another `facet-*` is forbidden.

Do not write the detailed chain order here. The sole source of detailed chain order is `## Ordering rationale`.

## S5 Domain Model

`## Domain model` must be layered:

- First-class business objects: business objects that can carry rules.
- Metrics/fields: formulas, progress indicators, amounts, goals, API fields, enumeration values, thresholds, etc.
- Display containers: pages, cards, lists, modals, API responses, notification carriers, etc.
- Object relationships: ownership, dependency, carrying, computation, display, lifecycle, or prerequisite relationships.
- State machines/state transitions: state, eligibility, phase, level, visibility, or amount changes.
- Boundary candidates: excluded, pending-migration, delivery-collaboration, implementation-support, or uncertain material.

The domain object within a closed-loop chain may only come from first-class business objects. Fields, formulas, pages, cards, APIs, and progress metrics must go into display containers/field anchors.

## S5 Ordering Rationale

Chain titles use plain text — no bold, no code style.

```markdown
## Ordering rationale

- Chain 1: <must match closed-loop chain 1 title exactly> — <why it comes first>
- Chain 2: <must match closed-loop chain 2 title exactly> — <why it follows>
```

Chain numbers and titles must exactly match those in `## Closed-loop decision chains`.

## S5 Closed-Loop Chain Block

Every closed-loop chain must use the following form:

```markdown
### Chain N: <title>

- Domain object: <must be listed under First-class business objects>
- State change: <state/eligibility/amount/visibility/phase change; if none write "no state change — display/validation/logging change only">
- Business action: <business action or business judgement>
- Display containers/field anchors: <display container or field from the model; if none write "no direct display container — source confirms back-end determination only">
- Applicable subject: <who>
- Trigger condition: <when/threshold/state/time window>
- Branches or actions:
  - <one branch or action>
  - <another branch or action>
- User-visible effect:
  - <one visible consequence>
- Linked open items: Issue N
- Evidence sources:
  - <source title or URL>
```

Rules:

- Unresolved words — `pending`, `TBD`, `unknown`, `to-be-confirmed` — must not remain in closed-loop commitments; they must be moved to `## Pending-decision critical issues`.
- If a closed-loop chain mentions a missing implementation, API, field, evidence, or detection method, it must write `Linked open items: Issue N`.
- Delivery/collaboration context must not become a closed-loop business rule; unless it directly changes a user-visible business commitment, it may only be demoted to a boundary, supporting evidence, or pending-decision issue.

When there are no closed-loop chains, use:

```markdown
## Closed-loop decision chains

No closed-loop decision chains have formed yet. Reason: <why the current sources cannot support a business commitment>.
```

## S5 Pending-Decision Block

Every pending-decision issue must support bidirectional binding:

```markdown
### Issue N: <issue title>

- Linked chain: Chain N
- Linked prerequisite domain: <use when there is no closed-loop chain or the issue precedes any chain>
- Decision point: <what needs to be decided>
- Current evidence: <what the sources have and have not proven>
- Pending confirmations: <what needs to be supplemented or asked>
- Suggested reviewer: <business / product / data / engineering role>
- Decision impact: <which rule, scope, field, state, display, or user commitment changes after confirmation>
```

When a closed-loop chain references an issue, the issue block must write `Linked chain`. Use `Linked prerequisite domain` only when the issue cannot yet be bound to a specific closed-loop chain.

## S5 Structured Detail Handoff

When an S3 proposition, a page-level structured-source signal, or S5 semantic re-mounting discovers tables, enumerations, field lists, mappings, formulas, thresholds, time windows, visible copy, numbers, tiers, levels, titles, or reward tiers that a reader may need to query, `## Structured detail handoff` must appear.

Every `###` subsection must use a table or a layered list. A subsection with only a paragraph description is non-compliant.

Table form:

```markdown
### <detail title> (full expansion)

| Item | Condition/field/state | Business meaning | Exception/pending | Source |
|---|---|---|---|---|
| <row identifier> | <source detail> | <decision meaning> | <exception or none> | <source> |
```

Layered-list form:

```markdown
### <detail title> (rule-compressed)

- Scope: <start/end or included set>
  - Generation rule: <formula, naming pattern, step, or grouping rule>
  - Endpoints and exceptions: <endpoints and exceptions>
  - Example: <one or two examples>
  - Source: <source>
```

Pending-confirmation subsections must also use a table or layered list to state what is missing and what changes when it is filled; writing only a paragraph summary is not acceptable.

## S7 Locale Brief: Required Sections

Every `*-domain-brief.md` must contain:

1. `## Overview & scope`
2. `## Out of scope`
3. `## Domain model summary`
4. `## Core business rules`
5. `## Key details` — when S5 has `## Structured detail handoff`
6. `## Terminology`
7. `## Pending confirmations`
8. `## Provenance`

S7 is based on S5 only. It may improve readability and target-locale expression, but must not add business semantics not present in S5 by drawing from S1/S3.

## S7 Domain Model Summary

Use layered labels:

```markdown
## Domain model summary

- **First-class business objects**
  - <object>: <reader-facing meaning>
- **Object relationships**
  - <relationship>
- **State machines/state transitions**
  - <state transition; if no stable state machine write "current sources have not formed a stable state machine">
```

## S7 Decision Cards

Every `###` subsection under `## Core business rules` must use the following card form:

```markdown
### Rule N: <reader-facing title>

- **Confirmed rule**
  - <carries only one decision point>
  - <another decision point>
- **Open boundary**
  - <boundary; if none write "current sources expose no additional boundary">
- **User-visible effect**
  - <one visible impact>
- **Linked open items**
  - <none, or points to an action item in ## Pending confirmations>
```

Rules:

- Each top-level bullet under `Confirmed rule` carries only one decision point. Do not compress multiple branches, phases, goals, rewards, or display consequences into a single bullet with semicolons.
- When a rule depends on threshold, state, field, level, copy, or other enumerable detail, the card states only the decision meaning; queryable detail goes into `## Key details`.
- Delivery/collaboration material must not enter `## Core business rules`.

## S7 Key Details

When `## Key details` is present, every `###` subsection must be queryable:

- Use a Markdown table for a finite set of rows that readers need to compare item by item.
- Use a layered list for rule-patterned ranges, naming schemes, or grouping detail.
- Writing only a paragraph summary is not acceptable.

## S7 Pending-Confirmation Action Index

`## Pending confirmations` must always contain these category headings, even when a category currently has no items:

- `### Domain boundary`
- `### Rule conflicts`
- `### Data & interface`
- `### Policy & presentation`
- `### Materials to supplement`

Every item must use the following layered action-item form:

```markdown
- **Affected rule**: <affected rule or topic>
  - **To confirm/supplement**: <what is missing>
  - **Suggested reviewer**: <confirming role>
  - **Post-confirmation impact**: <what changes after confirmation>
```

## S7 Language

- Main text uses `deliverable_locale` as its primary language (Simplified Chinese for `zh-CN`).
- Necessary English is allowed only as: source-name in parentheses, field/API/system name in backticks, an abbreviation already explained in `## Terminology`, or a source path/link in `## Provenance`.
- `## Terminology` (for zh-CN locale briefs) uses the form `Chinese term (English Term): explanation`; the first occurrence of a bilingual term in the body must use the same bilingual anchor.
- When a bilingual term appears in the body, the first occurrence must use the same bilingual anchor.
- Avoid internal-process jargon and deprecated slang defined in `domain-knowledge/language/s6-reader-language-policy.json`.
