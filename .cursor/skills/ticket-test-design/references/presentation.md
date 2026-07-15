# ticket-test-design · presentation contract

> Stacks with [`.cursor/rules/ticket_test_design.md`](../../../rules/ticket_test_design.md): substance from the rule; **readability** from this file.  
> Spoken deixis: [`../../_shared/presentation-p10.md`](../../_shared/presentation-p10.md).  
> Chinese locale: [`presentation.zh-CN.md`](./presentation.zh-CN.md).

## Essence

Readers are testers and PO/devs in a hurry. **Summary first**, then contracts (AC), then cases. Prefer **indented field blocks** (YAML-like) over tables and emoji theater.

## Laws P1–P12

| # | Law | Why |
|---|-----|-----|
| P1 | Open with `## Summary`: **Contract readiness** + **Pack note**, counts, residual risk | 60s decision; contract ≠ should pack |
| P2 | `## Acceptance` before cases; mark **proposed** visibly | Contract ≠ evidence |
| P3 | Short `## Design`: primary technique + one-line rationale + scan_checklist | Defensible cut |
| P4 | Group cases: `## Must` → `## Should` → `## Later` | Execution priority |
| P5 | Case header: `### TC-001 · must · <one-line title>` | Scannable + gateable |
| P6 | Case body = **indented keys** (`proves` / `supplements`, `given`, `when`, `then`, …) | Edit/diff friendly |
| P7 | `then` = one observable **per proved AC**; multi-AC ⇒ `(AC-n)` tags; weak → `oracle_confidence: weak` | Avoid bundled blame |
| P8 | `brief`: Summary + Acceptance + Must only; Should as bullet titles | Stand-up length |
| P9 | No emoji-required format; no “Layer 1/2/…” as section law | Avoid MECE theater |
| P10 | Shared deixis file for “this/that” ambiguity | [`presentation-p10.md`](../../_shared/presentation-p10.md) |
| P11 | Every `(given)` AC is must-proved or listed under **Must-deferred** | Contract → must invariant |
| P12 | Non-AC tests use `supplements:` — never stretch `proves` | Honest traceability |

## Recommended skeleton (English)

```markdown
# Test design: PROJ-123 — <feature one-liner>

## Summary

- **Scope**: …
- **Contract readiness**: contract-ready | blocked-by-ac-gaps | blocked-by-must-deferred | blocked-by-evidence
- **Pack note**: should recommended (N); may include weak oracles | should none
- **Counts**: must N · should N · later N
- **Residual risk**: …
- **Evidence gaps**: … (or none)

## Acceptance

- **Source**: jira | mixed | proposed
- **AC-1** `(given)`: …
- **AC-2** `(proposed)`: …   <!-- [PROPOSED] -->
- **Must-deferred**: (none) | `AC-n — reason` (forces non-ship readiness)

## Design

- **Primary**: state_transition
- **Secondary**: error_guessing
- **Rationale**: …
- **Scan**: security=needed · resilience=out_of_scope · exploratory=charter_only
- **Coverage intent**: …

## Scope

- **In**: …
- **Out**: …

## Must

### TC-001 · must · Purchaser amends open order quantity

    proves: [AC-1]
    automate: candidate
    technique: use_case
    level: ui
    smoke: true
    kind: happy
    given: Order is Open; quote_version not expired; user is purchaser
    when: Change an unshipped line quantity and save
    then: (AC-1) Line shows the new quantity after save
    data_deps: [seed Open order + valid quote]
    regression_touchpoints: [order totals, line PATCH]
    oracle_confidence: high
    notes: []

### TC-002 · must · Totals refresh after successful amend

    proves: [AC-5]
    automate: candidate
    technique: use_case
    level: ui
    kind: happy
    given: Same as successful amend preconditions
    when: Save a valid quantity change
    then: (AC-5) Order detail totals refresh within 3s
    oracle_confidence: high
    notes: []

## Should

### TC-010 · should · Non-purchaser cannot amend via API

    supplements: [security-role-gate]
    automate: candidate
    technique: error_guessing
    level: api
    kind: security
    given: …
    when: …
    then: …
    notes: [ASSUMPTION] …

## Later

- **charter**: Explore quantity-up after Partially Shipped — approval unclear
  - **why_later**: Ticket open question; needs PO
- **idea**: Pairwise browsers × roles
  - **why_later**: Not ship-blocking for this story

## Environment

    device: desktop (primary)
    browser: Chrome (primary); Safari note if unknown
    network: default office / not chaos unless in scope
```

## Field labels

Use English keys in the indented body (validator depends on them). Reader headings above may be localized via [`presentation.zh-CN.md`](./presentation.zh-CN.md).

| Key | Required on |
|-----|-------------|
| `proves` | every **must** case (direct entailment) |
| `supplements` | **should** (or rare must) when not AC-entailed |
| `automate` | every must/should: `candidate` \| `manual` \| `n/a` |
| `given` / `when` / `then` | every must/should case |
| `technique` | recommended |
| `data_deps` | when known |
| `regression_touchpoints` | when known — **omit** if unknown |
| `oracle_confidence` | when not obviously high |
| `notes` | assumptions / insufficient evidence |

## Anti-patterns

| Don’t | Do |
|-------|-----|
| Put a **given** AC only under Should | Must case (or Must-deferred + blocked Contract readiness) |
| Single `Readiness: ship-with-must+should` | Split **Contract readiness** + **Pack note** |
| `proves: [AC-1]` for a role/security case that AC-1 does not state | `supplements:` or a `(proposed)` AC |
| Bundle two ACs in one `then` without `(AC-n)` tags | One case per AC, or tagged multi-check `then` |
| Framework/POM detail in this skill | `automate: candidate|manual` only |
| Emoji Golden / MECE layer dumps | Indented keys under `### TC-…` |
| `Regression: N/A` padding | Omit the field |
