# DEMO-1 — Buyer can amend open order when quote is still valid

**Type:** Story  
**Status:** To Do  
**Agile Team:** Demo Product Team  
**Priority:** High  

## Summary

As a buyer purchaser, I want to amend line quantities on an open order while the linked quote is still valid, so that I do not have to cancel and recreate the order.

## Description

### Background

Buyers currently cancel and re-place orders when quantities change. Support wants amend-in-place for **open** orders only.

### Acceptance criteria

1. When an order is in status `Open` and its `quote_version` is not expired, the purchaser role can change line quantity and save.
2. When the quote is expired, Save is disabled and the portal shows a message that a new quote is required.
3. When the order is `Shipped` or `Cancelled`, amend controls are hidden.
4. Partial fulfillments: only unshipped lines remain editable; shipped lines are read-only.
5. After a successful amend, the buyer sees updated totals within 3 seconds on the order detail page.

### Out of scope

- Price renegotiation
- Adding new SKUs to an existing order
- WMS pick-path changes

### Open questions

- Should amend after `Partially Shipped` require seller approval? (Ticket does not say.)
- Exact copy for the expired-quote banner is TBD.

## Comments

- **PO:** Prefer no seller approval for quantity-down; quantity-up may need review — not decided.
- **Eng:** Reuse existing `PATCH /orders/{id}/lines` if AC fits; no API design attached.
