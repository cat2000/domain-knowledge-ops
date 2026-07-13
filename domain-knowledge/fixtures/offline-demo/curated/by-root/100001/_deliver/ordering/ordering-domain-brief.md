# Ordering and amendments · domain brief

> **Fixture only** — fictional Acme Orders. Not production tenant data.

## Overview and scope

- **Audience**: buyer purchaser, read-only observer
- **Scope**: amend line quantities on **Open** orders while the linked quote version is valid; read-only rules after fulfillment
- **Out of scope here**: price renegotiation, adding SKUs, WMS pick-path internals

## Out of scope (detail)

- Warehouse algorithms, internal on-call schedules, pure API field reconciliation tables

## Domain model summary

- **First-class objects**
  - **Order** — buyer-visible purchase commitment
  - **Quote Version** — governs whether place/amend pricing and validity apply
  - **Order Line** — smallest unit for quantity changes (when not yet shipped)
- **Relations**
  - Order **binds** one quote version
  - Order **contains** multiple order lines
- **State machine**
  - Open → Partially Shipped → Shipped; may → Cancelled at any time

## Core business rules

### Rule cluster · Amend quantity when Open and quote valid

- **Confirmed rule**
  - **Audience**: purchaser role
  - **Condition**: order status is `Open`; bound `quote_version` is not expired
  - **Branch**: allow editing quantity on unshipped lines and save; after save, order detail shows new quantities and totals
  - **Time window**: until quote validity end
  - **Exception**: none in this cluster
  - **User-visible effect**: editable quantity controls; totals refresh within 3 seconds after save
- **Open boundary**
  - Whether quantity **increase** requires seller approval (ticket undecided)
- **User-visible effect**
  - amend allowed vs save disabled with new-quote message
- **Linked open items**
  - See Open items · quantity-up approval

### Rule cluster · Expired quote blocks amend save

- **Confirmed rule**
  - **Audience**: purchaser
  - **Condition**: `quote_version` is expired
  - **Branch**: disable Save; show message that a new quote is required
  - **Time window**: effective immediately on expiry
  - **Exception**: none
  - **User-visible effect**: cannot save amendments; sees expiry prompt
- **Open boundary**
  - Exact banner copy (ticket TBD)
- **User-visible effect**
  - blocks amend save
- **Linked open items**
  - Expired banner copy

### Rule cluster · Shipped lines read-only

- **Confirmed rule**
  - **Audience**: purchaser
  - **Condition**: order is `Partially Shipped` or line already shipped
  - **Branch**: shipped lines read-only; unshipped lines remain editable under Open/valid-quote rules
  - **Time window**: n/a
  - **Exception**: when whole order is `Shipped` or `Cancelled`, all amend controls hidden
  - **User-visible effect**: some lines editable, some read-only, or no amend entry on closed orders
- **Open boundary**
  - Whether Partially Shipped always requires seller approval (ticket open question)
- **User-visible effect**
  - control visibility and read-only state
- **Linked open items**
  - Partial-ship approval

## Glossary

- **Quote Version** — contract price and validity identifier; after expiry, amend save at prior price is not allowed
- **Open** — order not yet in shipment; quantity amend eligible under this brief

## Open items

- **Affected rule**: Amend quantity when Open and quote valid
  - **Pending / needed**: whether quantity **increase** requires seller approval
  - **Suggested owner**: PO / seller operations
  - **Impact if confirmed**: may add approval branch or keep purchaser self-service
- **Affected rule**: Expired quote blocks amend save
  - **Pending / needed**: final expired-banner copy
  - **Suggested owner**: UX / PO
  - **Impact if confirmed**: copy only, no branch change
- **Affected rule**: Shipped lines read-only
  - **Pending / needed**: mandatory seller approval after Partially Shipped
  - **Suggested owner**: PO
  - **Impact if confirmed**: may add approval state

## Provenance

- Fixture ticket: `DEMO-1` (`domain-knowledge/fixtures/offline-demo/jira/DEMO-1.md`)
- Strategy example axis: ordering / quote validity (see `strategy.example.md`)
