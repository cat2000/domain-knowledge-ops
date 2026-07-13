# requirement-risk · DEMO-1 (sample)

> **Sample only** — illustrates refinement-depth output for the offline fixture. Run `@requirement-risk DEMO-1 team=demo` in Cursor for a live pass.

## Summary

**Scope**: Buyer purchaser amends line quantities on an **Open** order while the linked quote version is still valid; expired quote disables save; **Shipped** / **Cancelled** orders hide amend controls; partially shipped orders keep shipped lines read-only.

**One-liner**: Core amend paths are specified, but seller-approval rules for quantity-up and partial-ship edge cases are still open against the ordering brief.

**Must decide first**: Whether quantity increases need seller approval; whether amend after Partially Shipped needs approval; final expired-quote banner copy.

**Counts**: MUST FIX 2 · SHOULD CLARIFY 2 · optional 0  
**Readiness**: Ready with risks (`READY_WITH_RISKS`)

### MUST FIX highlights

1. **R-001 · Governance** — Quantity-up may need seller review per PO comment, but AC and brief list this as an open boundary; shipping without a branch risks building the wrong approval UX.
2. **R-002 · Governance** — Ticket open question on Partially Shipped approval is unresolved while brief also flags the same boundary; planners cannot commit to control flow.

---

### `FULL_UNKNOWN_MAP` — full risk map `R-###`

#### R-001 · MUST FIX · Governance / escalation / decision-rights misalignment

- Evidence: DEMO-1 comment — "quantity-up may need review — not decided"; ordering brief open item on quantity-increase approval [DOMAIN_KNOWLEDGE]
- Stakes: If engineering assumes no approval, quantity-up amends may bypass seller controls and require rework when PO confirms otherwise.
- Recommendation (D): Resolve now — PO decides self-service vs approval branch for quantity increase before sprint commitment.
- Suggested owner: Product owner

#### R-002 · MUST FIX · Governance / escalation / decision-rights misalignment

- Evidence: DEMO-1 open question — "Should amend after Partially Shipped require seller approval?"; brief open item on partial-ship approval [DOMAIN_KNOWLEDGE]
- Stakes: Partial-ship amend behavior affects which lines stay editable and whether a new workflow state is needed; deferring forces late UI/API churn.
- Recommendation (D): Resolve now — confirm whether Partially Shipped amends are purchaser self-service (unshipped lines only) or need seller gate.
- Suggested owner: Product owner

#### R-003 · SHOULD CLARIFY · Verifiability / acceptance / testability misalignment

- Evidence: AC #2 requires a message when quote expired; ticket lists "Exact copy for the expired-quote banner is TBD"; brief open item on banner copy [DOMAIN_KNOWLEDGE]
- Stakes: QA cannot sign off on copy-sensitive UX; minor if branch logic is fixed but still blocks UAT checklist closure.
- Recommendation (D): Defer with guardrails — ship branch logic with placeholder copy flagged for UX review before release.

#### R-004 · SHOULD CLARIFY · Contract / API / state / data semantics misalignment

- Evidence: Eng comment proposes `PATCH /orders/{id}/lines` reuse "if AC fits"; no API contract attached to ticket
- Stakes: Integrators may assume idempotent partial-line updates without defining error cases for expired quote or read-only shipped lines.
- Recommendation (D): Accept with explicit trigger — spike or attach API notes when implementation starts; align with brief state branches.

---

### `EVIDENCE_COVERAGE`

| Source | Used | Notes |
|--------|------|-------|
| Jira / fixture `DEMO-1.md` | Yes | Summary, AC, comments, open questions |
| Domain brief S7 `ordering-domain-brief.md` | Yes | Open/valid quote amend, expired quote, shipped-line read-only [DOMAIN_KNOWLEDGE] |
| Attribution `DEMO-1.attribution.yaml` | Yes | Primary slug `ordering` |
| Attachments | No | Fixture ticket has none |
| Confluence | No | Offline demo |
| Codebase | No | No anchors in ticket |

### `ASSUMPTION_REGISTER`

(empty)
