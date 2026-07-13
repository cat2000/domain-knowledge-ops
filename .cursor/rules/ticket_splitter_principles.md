Chinese locale: [`.cursor/rules/ticket_splitter_principles.zh-CN.md`](./ticket_splitter_principles.zh-CN.md)

# ticket_splitter_principles

## 0. How this file is used (read this first)

- **`ticket_system.md` is the only input to the runtime engine** (the model does not use this file when splitting).
- **This file is for people:** after a split is produced, use it to **judge quality** and to **review PRs** that change `ticket_system.md`.
- **R1, R2, R2.5, R3, R4, R5, R6, R7, R8, R9, R10** in section 3 and the **review questions** in section 5 are a **shared vocabulary** with `ticket_system.md` for "good decomposition," not a second prompt layer.
- **Intended use in chat (optional):** in a *follow-up* turn, @-mention this file, paste the decomposition (or point to the prior message with the `ticket_system` result), and ask to evaluate (e.g. compare against **section 3** and **section 5**). Nothing auto-triggers this; the user does it when they want a principles-based review.

## 1. Purpose

This document defines the **evaluation / review** layer for ticket splitting.

It exists to help humans answer:
- whether a **finished** decomposition is fundamentally sound
- which ideas are "core quality" versus optional runtime detail in `ticket_system.md`
- how to review a **proposed change** to `ticket_system.md` without accidentally lowering decomposition quality

**`ticket_system.md` encodes the operational "how" for the engine. This file encodes the "what good looks like" for people checking that output.**

---

## 2. Scope

These principles describe what **good decomposition-item-level** output looks like for delivery planning, for **human** review.

They are used to evaluate (after a split exists):
- whether a decomposition is fundamentally correct
- whether a change to `ticket_system.md` would preserve or weaken those outcomes
- whether a decomposition favors real delivery truth over internal neatness

These principles do NOT define:
- output formatting details
- exact wording for titles or fields
- prompt-specific procedural instructions
- low-level runtime heuristics unless they express a core principle

---

## 2.5 Review precedence (for humans assessing outputs or edits)

When you evaluate a **finished** split, or you judge a situation where ad-hoc user text, a long template, or pressure for "more items / more surface" conflicts with a sound decomposition:

1. **INVEST / `Testable` (and `source_requirement_note` correction)**—when present, it **wins** over "mirroring Jira wording" or "more items looks better." Good `done_when` and **clarity of how success is known** take priority over form-filling.
2. Treat **verification truth (R1)** and **evidence sufficiency before story expansion (R2.5)** as more important than how many items appear, how full a template looks, or narrative polish.
3. A decomposition should not earn a pass merely because it adds items to match an external template, polish granularity, or fill a format—check R1 and R2.5 first.

---

## 3. Core Principles

### R1. Verification Truth First

Decomposition must first serve the primary verification surface of the ticket.

The primary verification surface is the main place where truth is established:
- User Surface
- System Surface
- Contract Surface

When reviewing, check that the decomposition optimizes for the primary verification surface **before** internal neatness, code structure, or implementation convenience.

### R2. Smallest Complete Result First

Default to preserving the smallest complete result.

This may be:
- the smallest complete user-verifiable experience
- the smallest complete business action

Do not mechanically split a complete result into smaller technical or rule fragments if users or downstream systems would only consider the combined behavior to be complete.

### R2.5. Evidence Sufficiency Before Item Expansion

Do not expand a decomposition into multiple concrete items unless the input provides enough evidence to support that expansion.

Additional items should be created only when they have at least one independent basis:
- explicit textual basis
- independent acceptance basis
- independent risk basis
- independent state-progression basis

If such evidence is missing, a sound split **converges** to:
- one smallest complete item
- or one Spike plus one smallest MVP item

Reject expansions that promote common engineering considerations into standalone items **merely because they are plausible**, without independent basis.

### R3. Size Override

Completeness is the default, but not an absolute.

If the smallest complete result exceeds reasonable item size, it must be split.

Such splitting must preserve meaningful verification and must not fall back to arbitrary technical slicing.

Preferred forced split shapes include:
- independently meaningful sub-experiences
- main path before edge path
- rollout or enablement stages with independent value
- independently verifiable sub-actions

### R4. Real Progression Over False Phase Chains

Only real state progression justifies serialized phase decomposition.

A shared framework, module, scheduler, or execution point does not by itself create a true phase chain.

Serial dependencies are valid only when one slice must exist before another becomes valid, safe, or testable.

### R5. Orthogonal Dimensions Should Not Be Artificially Serialized

Independent rule dimensions attached to the same stable base should not be forced into a phase chain.

Examples include:
- trigger cadence
- data window
- stop condition
- retry policy
- display branch
- returned-field mapping

Shared base infrastructure is not enough to justify serialization.

### R6. Internal Consistency Is Secondary

Internal normalization, state unification, model cleanup, and similar internal improvements must not outrank externally verifiable results.

They may stand alone only when:
- they are themselves the primary verification surface
- or they truly block multiple externally verifiable slices and cannot be safely absorbed

### R7. Uncertainty Must Be Isolated Precisely

Spike is for uncertainty that materially changes decomposition, sequencing, correctness, or solution shape.

Spike is not for:
- generic discovery
- simple inventory work
- obvious implementation tasks
- work that can be safely absorbed into a non-Spike item

### R8. Observability Constrains Precision

Observability limits how precisely work may be decomposed with integrity.

High observability allows precise structural decomposition.
Low observability requires conservative slicing and forbids false precision.

When reviewing, flag splits that **pretend** to know internal structure that the evidence does not support.

### R9. Dependency Minimization

Dependencies must be minimized by default.

Prefer:
- no dependency
- validation dependency
- soft dependency

Use blocking only when downstream work is not valid or safe before upstream completion.

### R10. Use Rules, Don't Be Ruled by Them

Good decomposition **uses** available control surfaces to reduce blocking, reduce blast radius, and preserve mergeability.

Examples include:
- feature flags
- adapters
- compatibility layers
- fallback paths
- version coexistence
- mockable boundaries
- dual read / dual write
- cohort rollout

**Pattern-level examples (not exhaustive):** Strangler Fig, Branch by Abstraction, Anti-Corruption Layer (ACL), Published Language, Open Host Service. These **map to** the control means above (flags, adapters, boundaries, coexistence, mergeability)—they are **not** a separate **decomposition axis**; they do **not** replace primary-surface and smallest-complete-result logic.

This is not optional optimization.
It is part of good decomposition judgment.

---

## 4. Principle Priority

When principles conflict, prefer this order:

1. Verification Truth First
2. Smallest Complete Result First
3. Evidence Sufficiency Before Item Expansion
4. Size Override
5. Real Progression Over False Phase Chains
6. Orthogonal Dimensions Should Not Be Artificially Serialized
7. Observability Constrains Precision
8. Dependency Minimization
9. Uncertainty Must Be Isolated Precisely
10. Use Rules, Don't Be Ruled by Them
11. Internal Consistency Is Secondary

This priority order exists to prevent local optimizations from overriding the core purpose of decomposition.

`ticket_system.md` does not repeat this ordering; when **two principles seem to conflict** in a given output, use this list **at review time** to decide which concern should win, then judge whether the split matches that (or document why not).

---

## 5. Review Questions

Use these questions to review a decomposition or a proposed change to `ticket_system.md`:

1. Does the decomposition identify the correct primary verification surface?
2. Does the decomposition preserve the smallest complete result?
3. If it expanded into multiple items, does each added item have independent textual, acceptance, risk, or state basis?
4. If it split the smallest complete result, was the split forced by size rather than convenience?
5. Does the output confuse shared infrastructure with true phase progression?
6. Does the output serialize orthogonal rule dimensions unnecessarily?
7. Does the decomposition let internal consistency outrank externally verifiable value?
8. Does the decomposition introduce a Spike for real uncertainty, or for generic investigation?
9. Does the decomposition claim more structural precision than observability supports?
10. Does the decomposition create dependencies that could have been validation or soft instead?
11. Does the decomposition make active use of available control surfaces?
12. Does the decomposition avoid **orphan** prep whose main payoff is only internal neatness or a **generic** "domain model first / refactor first" **without** tying to **this** ticket's verifiable outcomes—**while still allowing** a **bounded** Tech Task (Enabler)-style refactor or shaping work when **current complexity genuinely blocks** adding the feature directly and the item has **clear scope and observable `done_when`** as an unblocker? Does it also avoid **mechanical** one-entity-one-item splits that fragment the **smallest complete verifiable** result? (R2, R2.5, R6)
13. Is **`source_requirement_note`** (when used) **INVEST-led**: does it **first** **correct** toward **Testable** (what "done" means and how it is checked), then align items, with **gaps to ideal** and **source caps** (e.g. dev-only, verify elsewhere) only **after** that? If the **source** prescribes a bad shape (e.g. dev vs testing as the main axis for the same outcome), does the output **avoid** mirroring it, and do items **embody** the INVEST-consistent split within evidence limits? (R1, R2, R2.5)
14. Does each item **title** read as a **one-primary-outcome promise headline** (one-breath refinement scan), rather than a comma-stacked dump of every `scope` change? (presentation P11; title quality does not equal auto-split)
15. Does each **`scope` bullet** state **one orally scannable concern**, rather than welding tab/filter/card facets with colons, semicolons, or slashes into a single inventory line? (presentation P12; rewrite bullets, not auto-split the Story)

---

## 6. Relationship to `ticket_system.md`

| Artifact | Role |
|----------|------|
| `ticket_system.md` | **Only** prompt the engine uses to produce a split. |
| `ticket_splitter_principles.md` (this file) | **After** a split is produced, humans use it to **assess quality** and to **review changes** to `ticket_system.md`. |

- When **reviewing a pull request** to `ticket_system.md`, use this file and section 5 to ensure the edit does not weaken the outcomes you care about (the R-labels in section 3, including **R2.5**).
- The engine does **not** read this file; there is no "principles override runtime at generation time." At **review** time, you may still say: "this output is poor because it violates R2.5 / R4," and adjust `ticket_system.md` in a follow-up if needed.
- **Naming alignment:** the `(R#)` tags inside `ticket_system.md` are local mnemonics. They are **conceptually aligned** with **R1, R2, R2.5, R3, ..., R10** in section 3 so reviewers and authors share the same language when discussing a split.
- **Joint-user-behavior (smallest user-verifiable experience):** In `ticket_system.md` **DEFINITIONS**, the rule that several conditions, controls, or actions can form **one** **smallest user-verifiable** experience is how **R2** (smallest complete result), **R4** (real progression only), and **R5** (orthogonal dimensions not falsely serialized) show up in the runtime. When reviewing a split against that text, also check **`ticket_system.md` Step 4 — thin-slice `Avoid` list** (e.g. groundwork-only first, standalone normalization, FE/BE-only splits) and **Step 7** (size and anti-over-split, including fragmenting one user experience by condition/frequency/action when they **jointly** define "done").
- **R10 and DDD / integration pattern names:** The pattern names listed under **R10** (Strangler Fig, Branch by Abstraction, ACL, Published Language, Open Host Service) **illustrate** the same **control** ideas as the concrete means in `ticket_system.md` **Step 5**. They are **triggers and vocabulary** for *when* to apply those means—**not** the main axis for how to *count* or *sequence* items. Wording is **aligned** with Step 5: use patterns to **recall** control surfaces, **not** to drive the split.
- **INVEST correction vs source text:** The runtime **`Primary intent`** puts **INVEST** (especially **Testable**) first; **`source_requirement_note`** is the main **correction** channel. Fidelity to a dev-only/verify-elsewhere cap is a **constraint**, not a substitute for each item's **observable** `done_when` where the source allows. **Code** (when user/session provides) may supply **anchors** to split by route/package/service—**no** invented module names. At review, **section 2.5** item 1, **section 5** Q13.
- **Backlog type mapping (human process):** runtime output should already use three item types: User Story, Tech Task (Enabler), and Spike. Classification rule: user-visible value slice -> User Story; pure migration/refactor/compatibility slice -> Tech Task (Enabler); uncertainty isolation slice -> Spike.
