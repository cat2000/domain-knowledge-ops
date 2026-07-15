# Technique selection (on demand)

Load when choosing `design.primary_technique`. Prefer **one** primary; add secondary only to close a real gap.

## Shape → primary

| If the ticket is mainly… | Primary | Typical secondary |
|--------------------------|---------|-------------------|
| User journey / AC examples | `use_case` / `scenario` | `error_guessing` |
| Numeric/string/date fields & limits | `ep_bva` | `error_guessing` |
| Interacting business rules (AND/OR) | `decision_table` | `ep_bva` |
| Explicit statuses / lifecycle | `state_transition` | `use_case` |
| ≥3 independent factors × ≥2 values | `pairwise` | explain reduction |
| Authz / PII / tenancy | keep primary from shape; raise **security** scan | abuse cases as should/must |
| Unclear oracle / discovery | keep scripted must thin; put depth in **later charters** | — |

## Agile Testing quadrants (intent only)

Use in `coverage_intent.notes` — **do not** force cases in every quadrant.

| Quadrant | Intent |
|----------|--------|
| Q1 | Tech-facing, guide coding (unit/contract) — usually out of this skill unless ticket is API-only |
| Q2 | Business-facing examples (AC proof) — default home for **must** |
| Q3 | Exploratory / journeys — **later** charters |
| Q4 | Technology-facing critique (perf, security, resilience) — **should/must** only when ticket risk warrants |

## MECE “five layers” (scan, not output chapters)

When drafting, silently ask:

1. Happy path covered in **must**?  
2. Material exceptions for this AC?  
3. Security needed or `out_of_scope`?  
4. Resilience needed or `out_of_scope`?  
5. Exploratory left as **charter**?

Do **not** emit Layer-1…Layer-5 section titles unless the user asks for that presentation.

## Pairwise / decision tables

- State the reduction strategy in Design or case `notes`.
- Never label a reduced set as exhaustive.
- Keep invalid combinations independent unless testing resilience explicitly.

## Partition residual (same AC)

When AC or QA notes list a set (filters, status tags, roles, …) **or field modes** (online vs offline location under one “location” AC):

| Layer | Duty |
|-------|------|
| **must** | One faithful instance → contract green |
| **should** | **Closed** residual: finite named partitions/modes, **or** Stage stopping rule (e.g. every filter with ≥1 hit); plus shared negatives (empty filter) |
| **later / Residual risk** | Name leftovers explicitly — don’t pretend must exhausted the set |

Forbid open shoulds (“tap more if data/time”). Do **not** spend should on out-of-scope shell UI before closed residual disposition.

## Interface level (not a pyramid product)

| AC shape | Prefer `level` |
|----------|----------------|
| Fields/status “match API” / gateway contract | `api` (optional thin `ui` for display) |
| Pure interaction / navigation / layout | `ui` |
| Pure rules without UI | `logic` |

Tag `level` when not obviously `ui`. Still **no** framework codegen in this skill.
