# ticket-test-design · presentation contract

> Stacks with [`.cursor/rules/ticket_test_design.md`](../../../rules/ticket_test_design.md): substance from the rule; **readability** from this file.  
> Spoken deixis: [`../../_shared/presentation-p10.md`](../../_shared/presentation-p10.md).  
> Chinese locale: [`presentation.zh-CN.md`](./presentation.zh-CN.md).

## Essence

Optimize for **start testing in ~60s**, not an evidence memo.

Readers need: Can we call Done? Which **must** cases to run? What is deferred?  
Traceability (why AC wording is fuzzy, fixture paths, quadrant jargon) is **secondary** — one short line or end matter.

Prefer **indented field blocks** (YAML-like) over tables and emoji theater.

## Laws P1–P16

| # | Law | Why |
|---|-----|-----|
| P1 | **Summary = decision board**: Contract readiness → Pack note → Counts first; each bullet ≤1 short sentence | 60s open-to-test |
| P2 | `## Acceptance` before cases; mark **proposed** visibly; AC = **where + act + observe** | Executable contract |
| P3 | Put `## Design` **after** Later (or omit in `brief`) — ≤4 short bullets | Design is for reviewers, not Stage runners |
| P4 | Group cases: `## Must` → `## Should` → `## Later` | Execution priority |
| P5 | Case header: `### TC-001 · must · <one-line title>` | Scannable + gateable |
| P6 | **Must core fields only by default**: `proves`, `automate`, `given`, `when`, `then` | Anti “risk-report notes” |
| P7 | `then` = one hard observable per AC; ban soft “or / offered / may” unless `oracle_confidence: weak` | Avoid false greens |
| P8 | `brief`: Summary + Acceptance + Must cores only | Stand-up length |
| P9 | No emoji Golden / MECE layer section titles | Avoid theater |
| P10 | Shared deixis | [`presentation-p10.md`](../../_shared/presentation-p10.md) |
| P11 | Every `(given)` AC must-proved or **Must-deferred** | Contract invariant |
| P12 | Non-AC tests use `supplements:` | Honest traceability |
| P13 | Optional fields (`technique`, `level`, `kind`, `data_deps`, `regression_*`, `notes`) **only when they change execution** | Cut noise |
| P14 | **Chat delivery = draft file** for Must: full indented GWT — **never** table-compress cases in chat | File≠chat gap |
| P15 | Reader prose locale consistent (`deliverable_locale` / user ask); keys stay English | Scan without CN/EN thrash |
| P16 | Ambiguity / old-route / branch debates → **one** short `notes` line or Later — not inside `when` | Keep scripts runnable |

## Summary budget (P1)

**Required (top, short):**

1. **Scope** — one clause  
2. **Contract readiness** — token only  
3. **Pack note** — one clause  
4. **Counts** — `must N · should N · later N`

**Optional (each ≤1 short line; no compound essays):**

- **Residual risk** — top ship risk only  
- **Evidence** — one path / `source=…` pointer (not a paragraph)  
- **Evidence gaps** — omit if none; else one line + TC id  

Do **not** narrate “why there is no formal AC” in Summary — that belongs in Acceptance notes or Later.

## Recommended skeleton

```markdown
# Test design: PROJ-123 — <feature one-liner>

## Summary

- **Scope**: Amend Open-order qty while quote valid; no price/SKU/WMS
- **Contract readiness**: contract-ready
- **Pack note**: should 1 (weak API role) — does not block contract Done
- **Counts**: must 6 · should 1 · later 2
- **Residual risk**: Seller approval on quantity-up TBD
- **Evidence**: offline-fixture · ordering S7

## Acceptance

- **Source**: jira
- **AC-1** `(given)`: On Open order with valid quote, purchaser changes line qty and saves → new qty shown
- **AC-2** `(given)`: On Open order with expired quote → Save disabled + “new quote required”
- **Must-deferred**: (none)

## Scope

- **In**: …
- **Out**: …

## Must

### TC-001 · must · Amend qty on Open + valid quote

    proves: [AC-1]
    automate: candidate
    given: Order Open; quote valid; role purchaser; unshipped line exists
    when: Change line quantity and save
    then: (AC-1) Line shows the new quantity

### TC-002 · must · Totals refresh after amend

    proves: [AC-5]
    automate: candidate
    given: Successful amend just saved (same as TC-001 setup)
    when: View order detail
    then: (AC-5) Totals update within 3s

## Should

### TC-011 · should · Non-purchaser denied on PATCH

    supplements: [security-role-gate]
    automate: candidate
    given: …
    when: …
    then: …
    notes: [ASSUMPTION] HTTP status TBD — confirm API contract

## Later

- **charter**: …
  - **why_later**: …

## Design

- **Primary**: state_transition
- **Rationale**: Status/quote gates drive eligibility
- **Scan**: security=needed · resilience=out_of_scope · exploratory=charter_only

## Environment

    device: desktop
    browser: Chrome
    network: default
```

## Field labels

English keys in the indented body (validator depends on them). Reader headings may be localized via [`presentation.zh-CN.md`](./presentation.zh-CN.md).

| Key | Required on |
|-----|-------------|
| `proves` | every **must** case |
| `supplements` | should when not AC-entailed |
| `automate` | every must/should |
| `given` / `when` / `then` | every must/should |
| `notes` | only when assumption/gap changes how to run (≤1 short line) |
| `technique` / `level` / `kind` / `data_deps` / `smoke` | optional — omit if default/obvious |

## Anti-patterns

| Don’t | Do |
|-------|-----|
| Summary essays on evidence / missing formal AC | Short decision board + one-line Evidence |
| AC as product rationale | AC as where + act + observe |
| `when`/`notes` explaining route ambiguity at length | One short `notes` or Later charter |
| Soft `then`: “offered or share sheet” | One outcome, or `weak` + note |
| Design/quadrants before Must | Design after Later |
| Chat tables that drop GWT | Paste same indented Must as the draft |
| Mix reader languages mid-AC list | One reader locale for AC + case prose |
| Put a **given** AC only under Should | Must (or Must-deferred) |
| Stretch `proves` onto nearby AC | `supplements:` |
