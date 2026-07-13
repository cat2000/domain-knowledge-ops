# DEMO-BILL-1 — Mid-cycle seat change shows prorated charge before confirm

**Type:** Story  
**Status:** To Do  
**Agile Team:** Demo Product Team  
**Priority:** High  

## Summary

As a workspace admin, I want to increase billed seats mid-cycle and see the prorated charge before I confirm, so that I do not get a surprise invoice.

## Description

### Acceptance criteria

1. When the subscription is `Active` and the plan allows seat changes, an admin can open **Change seats** and enter a new seat count greater than current seats.
2. Before confirm, the UI shows: new monthly recurring amount, prorated charge for the remainder of the current billing period, and next invoice date.
3. On confirm, seats update immediately for entitlement; the prorated amount appears on the next invoice as a separate line.
4. When the subscription is `PastDue` or `Canceled`, Change seats is disabled with a message to resolve billing first.
5. Decreasing seats below currently assigned users is blocked until users are unassigned.

### Out of scope

- Annual ↔ monthly plan switches
- Tax calculation engine changes
- Self-serve plan downgrades with feature loss

### Open questions

- Should seat decreases take effect immediately or at period end? (Ticket undecided.)
- Exact copy for PastDue disablement TBD.

## Comments

- **PO:** Prefer immediate entitlement on increase; decrease timing still open.
- **Finance:** Proration must be visible pre-confirm; no silent mid-cycle charge.
