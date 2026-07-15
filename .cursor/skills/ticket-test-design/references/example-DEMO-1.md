# Test design: DEMO-1 — Amend open-order quantities while quote is valid

## Summary

- **Scope**: Amend unshipped line qty on Open orders while quote valid; no price/SKU/WMS
- **Contract readiness**: contract-ready
- **Pack note**: should 1 (weak API role) — does not block contract Done
- **Counts**: must 6 · should 1 · later 2
- **Residual risk**: Quantity-up / partial-ship seller approval TBD
- **Evidence**: offline-fixture · ordering S7

## Acceptance

- **Source**: jira
- **AC-1** `(given)`: On Open order with valid quote, purchaser changes line qty and saves → new qty shown
- **AC-2** `(given)`: On Open order with expired quote → Save disabled + “new quote required”
- **AC-3** `(given)`: On Shipped or Cancelled order → amend controls hidden
- **AC-4** `(given)`: On Partially Shipped order → shipped lines read-only; unshipped editable
- **AC-5** `(given)`: After successful amend → order totals visible within 3s
- **Must-deferred**: (none)

## Scope

- **In**: Open + valid quote amend; expiry block; hide on Shipped/Cancelled; partial-ship editability; totals refresh
- **Out**: Price renegotiation; add SKUs; WMS; chaos/network faults

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
    given: Successful amend just saved (TC-001 setup)
    when: View order detail
    then: (AC-5) Totals update within 3s

### TC-003 · must · Expired quote blocks save

    proves: [AC-2]
    automate: candidate
    given: Order Open; quote expired; role purchaser
    when: Try to change quantity and save
    then: (AC-2) Save disabled; “new quote required” shown
    notes: [Assert intent if banner copy TBD]

### TC-004 · must · Shipped order hides amend controls

    proves: [AC-3]
    automate: candidate
    given: Order Shipped; role purchaser
    when: Open order detail
    then: (AC-3) Amend controls not visible

### TC-005 · must · Cancelled order hides amend controls

    proves: [AC-3]
    automate: candidate
    given: Order Cancelled; role purchaser
    when: Open order detail
    then: (AC-3) Amend controls not visible

### TC-006 · must · Partial ship — only unshipped lines editable

    proves: [AC-4]
    automate: candidate
    given: Partially Shipped; mixed shipped/unshipped lines; quote valid; purchaser
    when: Try edit on each line
    then: (AC-4) Shipped read-only; unshipped editable

## Should

### TC-011 · should · Non-purchaser denied on PATCH

    supplements: [security-role-gate]
    automate: candidate
    given: Order Open; quote valid; non-purchaser (read-only observer)
    when: PATCH /orders/{id}/lines
    then: Request denied; line qty unchanged
    notes: [ASSUMPTION] Confirm 401/403 vs API contract

## Later

- **charter**: Quantity-up after Partially Shipped — seller approval?
  - **why_later**: Ticket open question; no false oracle
- **idea**: Qty boundaries if API/UI limits appear
  - **why_later**: No numeric limits in ticket/brief

## Design

- **Primary**: state_transition
- **Rationale**: Order/quote/line shipment states drive eligibility
- **Scan**: security=needed · resilience=out_of_scope · exploratory=charter_only

## Environment

    device: desktop
    browser: Chrome
    network: default
