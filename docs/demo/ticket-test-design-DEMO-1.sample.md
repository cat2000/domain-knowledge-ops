# ticket-test-design · DEMO-1 (sample)

> **Sample only** — illustrates Contract readiness + must/should/later for the offline fixture. Run `@ticket-test-design DEMO-1 team=demo` in Cursor for a live pass. Gate: `python3 scripts/jira/attachments/validate_ticket_test_design.py <draft.md>`.

# Test design: DEMO-1 — Amend open-order quantities while quote is valid

## Summary

- **Scope**: Purchaser amends unshipped line quantities on eligible orders; quote/status gates; no price/SKU/WMS work
- **Contract readiness**: contract-ready
- **Pack note**: should recommended (1); includes weak-oracle API role check — does not block contract Done
- **Counts**: must 6 · should 1 · later 2
- **Residual risk**: Quantity-up / Partially Shipped seller-approval still undecided (PO); expired-banner copy TBD
- **Evidence gaps**: API deny codes for non-purchaser not specified — see TC-011
- **Evidence**: `source=offline-fixture` · `domain-knowledge/fixtures/offline-demo/` · brief `ordering` S7 · attribution `primary=ordering`

## Acceptance

- **Source**: jira
- **AC-1** `(given)`: Order `Open` + `quote_version` not expired → purchaser can change line quantity and save
- **AC-2** `(given)`: Quote expired → Save disabled + message that a new quote is required
- **AC-3** `(given)`: Order `Shipped` or `Cancelled` → amend controls hidden
- **AC-4** `(given)`: Partial fulfillments → only unshipped lines editable; shipped lines are read-only
- **AC-5** `(given)`: After successful amend, updated totals visible within 3s on order detail
- **Must-deferred**: (none)

## Design

- **Primary**: state_transition
- **Secondary**: use_case, error_guessing
- **Rationale**: Eligibility is driven by order/quote/line shipment states
- **Scan**: security=needed · resilience=out_of_scope · exploratory=charter_only
- **Coverage intent**: Q2 proves each given AC; Q4 role check as supplements; Q3 charter for approval ambiguity

## Scope

- **In**: Quantity amend under Open + valid quote; expiry block; hide on Shipped/Cancelled; partial-ship editability; totals refresh
- **Out**: Price renegotiation; add SKUs; WMS; chaos/network faults

## Must

### TC-001 · must · Purchaser amends quantity on Open order with valid quote

    proves: [AC-1]
    automate: candidate
    technique: use_case
    level: ui
    smoke: true
    kind: happy
    given: Order status Open; bound quote_version not expired; role purchaser; at least one unshipped line
    when: Change that line quantity and save
    then: (AC-1) Line shows the new quantity after save
    data_deps: [seed Open order + valid quote + purchaser user]
    regression_touchpoints: [line quantity display]
    oracle_confidence: high
    notes: []

### TC-002 · must · Totals refresh after successful amend

    proves: [AC-5]
    automate: candidate
    technique: use_case
    level: ui
    smoke: true
    kind: happy
    given: Order Open; quote valid; role purchaser; amend just saved successfully
    when: Observe order detail after save
    then: (AC-5) Updated totals are visible within 3 seconds
    data_deps: [same as TC-001]
    oracle_confidence: high
    notes: []

### TC-003 · must · Expired quote disables save and prompts for new quote

    proves: [AC-2]
    automate: candidate
    technique: state_transition
    level: ui
    smoke: true
    kind: exception
    given: Order status Open; bound quote_version expired; role purchaser
    when: Attempt to change line quantity and save
    then: (AC-2) Save is disabled and the portal shows that a new quote is required
    data_deps: [seed Open order + expired quote]
    oracle_confidence: high
    notes: [Exact banner copy TBD — assert intent, not final wording]

### TC-004 · must · Shipped order hides amend controls

    proves: [AC-3]
    automate: candidate
    technique: state_transition
    level: ui
    kind: exception
    given: Order status Shipped; role purchaser
    when: Open order detail
    then: (AC-3) Amend controls are not visible
    data_deps: [seed Shipped order]
    oracle_confidence: high
    notes: []

### TC-005 · must · Cancelled order hides amend controls

    proves: [AC-3]
    automate: candidate
    technique: state_transition
    level: ui
    kind: exception
    given: Order status Cancelled; role purchaser
    when: Open order detail
    then: (AC-3) Amend controls are not visible
    data_deps: [seed Cancelled order]
    oracle_confidence: high
    notes: []

### TC-006 · must · Partially shipped — only unshipped lines editable

    proves: [AC-4]
    automate: candidate
    technique: state_transition
    level: ui
    kind: exception
    given: Order Partially Shipped with shipped + unshipped lines; quote still valid; role purchaser
    when: Inspect both lines and attempt to edit each
    then: (AC-4) Shipped lines are read-only; unshipped lines remain editable
    data_deps: [seed partial fulfillment + valid quote]
    oracle_confidence: high
    notes: []

## Should

### TC-011 · should · Non-purchaser cannot amend via API

    supplements: [security-role-gate]
    automate: candidate
    technique: error_guessing
    level: api
    kind: security
    given: Order Open; quote valid; authenticated non-purchaser (read-only observer per brief)
    when: Call PATCH /orders/{id}/lines to change quantity
    then: Request is denied and order line quantity is unchanged
    data_deps: [observer/read-only user; Open order]
    oracle_confidence: weak
    notes: [ASSUMPTION] Exact HTTP status not in ticket — confirm 401/403 against API contract; if skipped: role gate may be UI-only]

## Later

- **charter**: Quantity-up after Partially Shipped — does seller approval apply?
  - **why_later**: Ticket open question; PO undecided — do not script a false oracle
- **idea**: Boundary values on quantity (0, negative, max) if field limits appear in API/UI spec
  - **why_later**: No numeric limits in ticket or brief

## Environment

    device: desktop (primary)
    browser: Chrome (primary)
    network: default; chaos out of scope for this story
