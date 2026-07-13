# ticket-splitter · DEMO-1 (sample)

> **Sample only** — illustrates INVEST-style slices for the offline fixture. Run `@ticket-splitter DEMO-1 team=demo` in Cursor for a live pass.

**Scope**: Enable purchaser amend of line quantities on **Open** orders while quote version is valid, with correct blocking/hiding for expired quote, terminal order states, and partially shipped lines.

## Split overview

- **4 items**: Spike 1 → User Story 1 → User Story 2 → User Story 3
- **Blocking**: Spike 1 (approval rules) should complete before final UX on quantity-up / partial-ship flows
- **Optional**: none — no separate enabler unless API contract work is split by the team later

**Correction note**

The ticket mixes clear state branches with undecided approval policy. Split assumes **confirmed brief rules** for Open + valid quote, expired quote, and shipped-line read-only, while Spike 1 resolves governance gaps called out in DEMO-1 open questions and the ordering brief.

---

### Spike 1 (Spike)

**Title**: Confirm amend approval rules for quantity-up and partial ship

**Scope**

- Facilitate PO decision on whether quantity **increase** requires seller approval (DEMO-1 comment + brief open item)
- Confirm whether amend after **Partially Shipped** stays purchaser self-service on unshipped lines only, or needs seller approval
- Document outcome as amend-eligibility matrix: order status × quote validity × line ship state

**Acceptance (done_when)**

- Written decision recorded in ticket or brief open-item closure, covering quantity-up and partial-ship cases
- Ordering brief open items updated or explicitly deferred with guardrails referenced by downstream stories

**Depends**

- Links to R-001 / R-002 if same-session `@requirement-risk` was run

**Confidence**

- Medium — evidence exists but decision is missing

---

### User Story 1 (User Story)

**Title**: Purchaser changes quantity on open order with valid quote

**Scope**

- Purchaser role on order in `Open` status with non-expired `quote_version`
- Edit quantity on unshipped lines and save
- Order detail shows updated line quantities and totals within 3 seconds after successful save

**Acceptance (done_when)**

- Given Open order and valid quote, purchaser saves a quantity change on an unshipped line and sees updated totals on order detail within 3 seconds
- Quantity-down path works without seller approval unless Spike 1 mandates otherwise (then story respects Spike outcome)

**Depends**

- Spike 1 outcome for quantity-up branch

**Confidence**

- High — aligned with AC #1 and AC #5 [DOMAIN_KNOWLEDGE]

---

### User Story 2 (User Story)

**Title**: Block amend save when quote version expired

**Scope**

- When bound `quote_version` is expired, Save is disabled for amend flow
- Portal shows purchaser-visible message that a new quote is required (copy may be placeholder until UX supplies final text)

**Acceptance (done_when)**

- Given Open order with expired quote, purchaser cannot save line quantity changes and sees the new-quote-required message
- No successful amend API call occurs when quote is expired

**Depends**

- None for branch logic; copy may follow UX ticket

**Confidence**

- High — AC #2 and brief expired-quote cluster [DOMAIN_KNOWLEDGE]

---

### User Story 3 (User Story)

**Title**: Hide or read-only amend controls by order and line ship state

**Scope**

- `Shipped` or `Cancelled` orders: amend controls not shown
- `Partially Shipped` orders: shipped lines read-only; unshipped lines follow Open/valid-quote edit rules from User Story 1
- Respects Spike 1 if partial-ship amend needs seller approval

**Acceptance (done_when)**

- Given Shipped or Cancelled order, purchaser does not see amend entry points (AC #3)
- Given Partially Shipped order, shipped lines cannot be edited; unshipped lines behave per Spike 1 and valid-quote rules (AC #4)
- UI state matches order status and per-line fulfillment state without allowing edits on ineligible lines

**Depends**

- User Story 1; Spike 1 for partial-ship approval variant

**Confidence**

- High for read-only/hide rules; medium where Spike 1 adds approval branch [DOMAIN_KNOWLEDGE]
