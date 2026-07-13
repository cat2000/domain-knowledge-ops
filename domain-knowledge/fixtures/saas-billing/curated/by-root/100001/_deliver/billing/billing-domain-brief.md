# Subscription billing · domain brief

> **Fixture only** — fictional Northwind Billing. Not production tenant data.

## Overview and scope

- **Audience**: workspace admins, finance operators (read-only invoice view)
- **Scope**: mid-cycle seat increases on an **Active** subscription with visible proration before confirm
- **Out of scope**: plan switches, tax engine, feature-gated downgrades

## Not covered in this document

- Payment gateway retries, dunning email templates, internal ledger postings

## Domain model summary

- **First-class objects**
  - **Subscription** — billed workspace entitlement container
  - **Seat pool** — count of billable seats vs assigned users
  - **Invoice line** — recurring and prorated charges shown to the buyer
- **Object relations**
  - Subscription **owns** a seat pool
  - Subscription **generates** invoice lines each period
- **State machine / transitions**
  - Active → PastDue → Active; Active → Canceled; Canceled is terminal for seat changes

## Core business rules

### Rule cluster · Active subscription can increase seats with proration preview

- **Confirmed rule**
  - **Audience**: workspace admin
  - **Condition**: subscription status is `Active`; plan allows seat changes; new seat count > current seats
  - **Branches**: show Change seats; on draft change, display new MRR, prorated amount for remainder of period, and next invoice date; on confirm, update seat entitlement immediately and schedule prorated line on next invoice
  - **Time window**: proration from confirm timestamp to period end
  - **Exceptions**: none in this cluster
  - **User-visible effect**: admin sees preview totals before confirm; seats usable immediately after confirm
- **Open boundary**
  - Whether finance must approve increases above a threshold (ticket silent)
- **User-visible effect**
  - Preview required; no silent mid-cycle charge
- **Linked open items**
  - Finance approval threshold

### Rule cluster · PastDue or Canceled blocks seat changes

- **Confirmed rule**
  - **Audience**: workspace admin
  - **Condition**: subscription is `PastDue` or `Canceled`
  - **Branches**: disable Change seats; show resolve-billing message
  - **Time window**: immediate while status holds
  - **Exceptions**: none
  - **User-visible effect**: control disabled with explanatory message
- **Open boundary**
  - Exact PastDue copy (TBD)
- **User-visible effect**
  - Blocks seat changes until billing health restored
- **Linked open items**
  - PastDue banner copy

### Rule cluster · Cannot decrease seats below assigned users

- **Confirmed rule**
  - **Audience**: workspace admin
  - **Condition**: requested seat count < currently assigned users
  - **Branches**: block decrease; require unassign first
  - **Time window**: none
  - **Exceptions**: none
  - **User-visible effect**: validation error naming assigned-user count
- **Open boundary**
  - Whether allowed decreases apply immediately or at period end (ticket undecided)
- **User-visible effect**
  - Prevents orphaning assigned users
- **Linked open items**
  - Decrease effective timing

## Terminology notes

- **Proration** — charge for the unused portion of the billing period when seats increase mid-cycle
- **MRR** — monthly recurring revenue amount after the seat change
- **Active** — paid, in-good-standing subscription that may change seats

## Open items

- **Affected rule**: Active seat increase
  - **Pending**: finance approval threshold for large increases
  - **Suggested owner**: PO / Finance
  - **Impact once confirmed**: may add approval branch
- **Affected rule**: PastDue block
  - **Pending**: final disablement copy
  - **Suggested owner**: UX / PO
  - **Impact once confirmed**: copy only
- **Affected rule**: Seat decrease
  - **Pending**: immediate vs period-end effective date
  - **Suggested owner**: PO
  - **Impact once confirmed**: may defer entitlement drop

## Provenance

- Fixture ticket: `DEMO-BILL-1` (`domain-knowledge/fixtures/saas-billing/jira/DEMO-BILL-1.md`)
- Strategy portability sample: see `INDUSTRY.md` in this folder
