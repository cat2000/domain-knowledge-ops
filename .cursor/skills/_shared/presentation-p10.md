# Deixis & spoken team language (P10)

> Readers: `@requirement-risk`, `@ticket-splitter`.  
> Principle: sound like a refinement standup — what we’re doing, where it stops, what is scheduled elsewhere — not internal abbreviations.  
> Chinese locale examples remain valid in stakeholder-facing output.

## How to refer to the work

| Priority | Pattern | Example |
|----------|---------|---------|
| 1 | Say the work directly | “Add DBL contract upload + info form…” |
| 2 | “This change / this requirement” | “This change excludes CS approval…” |
| 3 | Issue key when traceability matters | “PROJ-123 covers upload UI only…” |
| 4 | “Story” when audience is engineers | “Done boundary for this Story is…” |

**Avoid**: “this ticket’s scope:”, repeating “this ticket” ≥2× when the title already has the key.

## Out of scope / boundaries (results, not calques)

State **which observable result this delivery stops at** and **who schedules the rest** (new Story, Epic child, next iteration).

| Avoid (calque jargon) | Prefer (result boundary) |
|-----------------------|--------------------------|
| “Full cancel enrollment flow / closed loop / persist” | **Does not include** enrollment becoming Cancelled and downstream quota/order handling (see PROJ-xxxx) |
| “Full xxx pipeline” | **Does not achieve** observable state Y; stops at X |
| “Follow-up ticket” slang | **Open a separate Story** / schedule next iteration |
| “Parent Epic follow-up” | **Schedule another item under the Epic** |
| “Brief follow-up” | **Open a task to update the domain brief** (who/when) |

## In done_when / correction notes

Write observable follow-ups (“conclusion in comments + **open a Story** to update the brief”), not “emit follow-up list” or “run the full xxx pipeline”.
