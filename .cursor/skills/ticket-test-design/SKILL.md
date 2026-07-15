---
name: ticket-test-design
description: >-
  Design release-confidence test cases for one Jira story: must/should/later
  cut, AC traceability, ISTQB technique selection without checklist theater.
  Triggers: @ticket-test-design, Jira key, pasted AC, brief, mode=analysis,
  focus=security, or after @requirement-risk / @ticket-splitter on the same key.
  Reads domain briefs as evidence only; does not write curated.
disable-model-invocation: true
---

# ticket-test-design (single-ticket test spec)

## First principles

**Artifact:** a **ship/Done proof pack** a tester can **start running in ~60s** — not an evidence memo.

**Quality:** every **`(given)` AC** has a **decidable must** (observable + oracle + seed) or **Must-deferred** / blocked readiness; **must = contract instance**, not partition exhaustion; **same-AC residual** disposed **closed**; **lowest stable `level`** that entails the AC; scan `needed` ⇒ closed disposition; should spend residual before chrome; honest `automate`. Presentation: short Summary, executable GWT, Design at end, **chat = draft**. Never invent product facts or framework code. **Not** a release-regression / metrics / NFR platform.

| | `@requirement-risk` | `@ticket-splitter` | This skill |
|--|---------------------|--------------------|------------|
| Job | Sprint decision input | INVEST backlog slices | **Test evidence for Done/ship** |
| Cut axis | MUST/SHOULD/OPTIONAL severity | Item boundaries | **must / should / later** anchored to **given AC** |
| Gate | Structure + counts | Testable `done_when` | Counts + given-AC coverage + contract/pack + `automate` |

**Corollaries**

1. No human confirm loop by default (`mode=analysis` is the exception).
2. Scripts check countable invariants (given-AC→must). They do **not** judge should priority — **agent must** apply should spend order + anti-padding from the rule.
3. Substance: [`../../rules/ticket_test_design.md`](../../rules/ticket_test_design.md). Readability: [`references/presentation.md`](references/presentation.md).

## When to use / not

| Use | Do not use → instead |
|-----|----------------------|
| Design cases for one ticket before/during QA | Readiness only → `@requirement-risk` |
| Trace cases to AC / `done_when` | Split backlog → `@ticket-splitter` |
| Cut infinite design space for release | Write Playwright/API automation → dedicated automation skill |
| Offline `DEMO-*` rehearsal | Refresh briefs → `@generate-knowledge-from-wiki` |

## How to invoke

```text
@ticket-test-design DEMO-1 team=demo
@ticket-test-design PROJ-123
@ticket-test-design team=<key> PROJ-123 brief
@ticket-test-design PROJ-123 mode=analysis
@ticket-test-design PROJ-123 focus=security
```

Or paste requirement / AC text.

| Param | Values | Default |
|-------|--------|---------|
| `team` | key/alias in `team-roots.json` | attribution / Agile Team |
| `brief` | short-mode words in message | full spec |
| `mode` | `analysis` | generate cases |
| `focus` | `security` | baseline scan |

Offline: [`../_shared/offline-demo.md`](../_shared/offline-demo.md). Team→root: [`../_shared/team-root.md`](../_shared/team-root.md).

## Workflow

```text
Jira key or text?
├─ DEMO-* / offline → fixtures; no network
├─ real key → issue + attachments (MCP or fetch_jira_attachments.py)
├─ Resolve team/root → S7 locale brief as evidence (note if only S6/draft)
├─ Build acceptance (jira → split done_when → proposed)
├─ Pick primary technique (+ secondary if needed) — see technique-selection
├─ For each given AC: decidable must + closed residual + level
├─ mode=analysis? → deliver scope/design/acceptance → STOP
├─ Draft → .jira_attachments/<KEY>/test_design_draft.md (Environment: build + seed)
└─ validate → fix → deliver in chat **same Must GWT as the draft**
```

## Responsibility

| Layer | Agent | Script |
|-------|-------|--------|
| Evidence | Briefs, dual-root, risk refs | Fetch issue/attachments |
| Generate | AC, cases, charters; **decidability**, **level**, **should spend**, scan disposal | No prose authorship |
| Gate | Fix reported failures only | `validate_ticket_test_design.py` (incl. given-AC coverage) |
| Soft should priority | **Agent** (rule spend order + anti-padding) + human reader | No |

## Gate rules

1. Pass validator before claiming done (full and `brief`).
2. Summary counts must match case headings (`must` / `should` / `later`).
3. Summary has **Contract readiness** + **Pack note** (no legacy single Readiness line).
4. Every **`(given)` AC** appears in some must `proves` **or** under **Must-deferred** (blocked contract readiness).
5. Every **must** case has honest `proves:`; multi-AC ⇒ `(AC-n)` in `then`; must/should have `automate:`.
6. **should** uses `proves` or `supplements:`; `later` = charter/idea only; never write `curated/`.

## Agent checklist

1. Load evidence per rule + [`../../contracts/jira-issue-domain-knowledge-context.md`](../../contracts/jira-issue-domain-knowledge-context.md).
2. List all **`(given)`** AC; plan **one decidable must** each (oracle + seed); list partition sets **and field modes**; plan **closed** residual disposition.
3. Set **Contract readiness** from given-AC must coverage **and decidability**; put should/weak oracles in **Pack note**.
4. Choose **`level`** (api/logic/ui) per lowest stable interface; don’t default data ACs to UI-only.
5. **Should spend order:** same-AC residual (closed) → weak-oracle hardening → security/resilience supplements → chrome last.
6. If scan `security|resilience: needed` → closed disposition (should/later/risk).
7. Write Must cores; Design after Later; Environment with device/build + `seed:` when shared; Summary = decision board.
8. Honest `automate`; draft → validate → **paste full indented Must in chat**.
9. Optional handoff: `@requirement-risk` / `@ticket-splitter` / automation skill — not codegen here.

## Done when

- [ ] Validator exit 0 (or explicitly marked failed)
- [ ] Summary decision board readable in ≤60s
- [ ] Every given AC covered by decidable must or Must-deferred / blocked-by-evidence
- [ ] Same-AC residuals disposed **closed**
- [ ] Scan `needed` disposed or truly `out_of_scope`
- [ ] Environment names how to run (build + seed if needed); chat = draft
- [ ] Honest `automate` + sensible `level`; no stretch `proves`; no full-coverage claim

## Forbidden

- MECE five-layer dumps / emoji Golden / table-compressed Must in chat
- Summary evidence essays; Design before Must
- Soft `then` without `oracle_confidence: weak`
- Open residual shoulds; chrome should before same-AC residual
- Undecidable must + `contract-ready`; `needed` scan with no disposition
- Quantity quotas; inventing AC/steps; framework codegen
- Expanding into release packs / metrics / default NFR-chaos platforms
- Skip gate; confirm ritual unless `mode=analysis` / ungated draft requested

## References (progressive)

- Presentation: [`references/presentation.md`](references/presentation.md) · zh: [`references/presentation.zh-CN.md`](references/presentation.zh-CN.md)
- Technique selection: [`references/technique-selection.md`](references/technique-selection.md)
- Golden readable example: [`references/example-DEMO-1.md`](references/example-DEMO-1.md) (mimic hierarchy; not emoji theater)
- P10 deixis: [`../_shared/presentation-p10.md`](../_shared/presentation-p10.md)

## Examples

```text
@ticket-test-design DEMO-1 team=demo
→ offline fixture → draft → validate → readable spec

@ticket-test-design PROJ-123 brief
→ summary + AC + must only → validate --brief
```
