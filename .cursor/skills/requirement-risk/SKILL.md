---
name: requirement-risk
description: >-
  Use when refining a single Jira story for readiness, risk, or decision blockers
  before sprint commitment. Triggers: @requirement-risk, Jira key (e.g. PROJ-123),
  pasted requirement text, stage/focus/brief, pre-sprint or security scan.
  Reads domain briefs as evidence only; does not write curated.
disable-model-invocation: true
---

# requirement-risk (single-ticket readiness)

## First principles

**Artifact**: sprint **decision input** — in ~30s the reader knows what to do, whether to commit, and what to decide first. Optimize **decision latency**, not risk-item count.

**Quality**: every `R-00N` needs **evidence, stakes, and an actionable disposition (D)**; counts must match title severities. Never invent product facts from the domain library that Jira does not support; ticket vs brief conflicts are listed side-by-side, not silently resolved.

| | Wiki `@generate-knowledge-from-wiki` | `@ticket-splitter` | This skill |
|--|--------------------------------------|--------------------|------------|
| Cost of error | Pollutes library briefs | Planning backlog churn | Wrong decision order / missed MUST |
| Who stops bad output | Human confirms module cuts | Scripts block fake testability | **Scripts** block count/structure/jargon drift |
| Loop | Prep → confirm → compose | Draft → gate → fix | **Draft → gate → fix** (no human gate in the loop) |

**Corollaries**

1. Do **not** wait for human confirm by default; review happens when reading the report.
2. Borrow from wiki **“scripts verify explicit form + fail must fix”** — not checklist / confirm / continue ritual.
3. Scripts do **not** decide “should this be MUST”; they check countable signals.
4. Semantics from `requirement_risk.md`; presentation: [`references/presentation.md`](references/presentation.md).

## When to use

- Refinement / pre-sprint readiness for one Jira issue
- Readiness call (ready / risky-but-ok / blocked)
- Domain briefs may exist under `curated/by-root/<root_id>/`

## When not

| Scenario | Use |
|----------|-----|
| Refresh wiki / write briefs | `@generate-knowledge-from-wiki` / `@distill-domain-knowledge` |
| Sprint bulk into briefs | `@add-knowledge-from-jira` |
| Split only | `@ticket-splitter` |
| No library + thin ticket | Still run; mark evidence gaps; do not invent modules |

## How to invoke

- `@requirement-risk DEMO-1 team=demo` (**offline demo**, no `.env` / network)
- `@requirement-risk PROJ-123`
- `@requirement-risk team=<key> PROJ-123`
- `@requirement-risk PROJ-123 stage=pre_sprint focus=security`
- `@requirement-risk PROJ-123 brief`
- Or `@requirement-risk` + pasted requirement text

Offline `DEMO-*`: follow [`../_shared/offline-demo.md`](../_shared/offline-demo.md); **no** Jira calls.

| Param | Values | Default |
|-------|--------|---------|
| `team` | any key/alias in `team-roots.json` | attribution / Agile Team |
| `stage` | `intake` / `refinement` / `pre_sprint` | `refinement` |
| `focus` | `risk` / `scope` / `security` | full baseline |
| `brief` | message contains `brief` / short-mode words | full Layer 2 |

Team → root: [`../_shared/team-root.md`](../_shared/team-root.md).

## Preconditions & failures

- **Offline `DEMO-*`**: no credentials — [`../_shared/offline-demo.md`](../_shared/offline-demo.md)
- **Real keys**: `.env` `JIRA_*` or `ATLASSIAN_EMAIL` / `ATLASSIAN_API_TOKEN`
- **Network**: real keys need Jira; attachments via `python3 scripts/jira/attachments/fetch_jira_attachments.py <KEY>`
- No credentials → paste body or use `DEMO-1`
- Attachment fetch fail → mark in `EVIDENCE_COVERAGE`; do not guess
- No brief → still emit; mark missing library anchors
- Gate fail → fix and re-run; **do not** claim done without pass

## Decision tree

```text
Jira key?
├─ DEMO-* (or offline/fixture) → fixtures/offline-demo; skip network
├─ real key → MCP has attachment bytes?
│       ├─ no → fetch_jira_attachments.py
│       └─ yes → use MCP
├─ Resolve team/root (user team= > attribution > Agile Team > keywords)
├─ Business brief root vs Agile Team root aligned?
│       ├─ yes → read _deliver/<slug>/* brief (S6)
│       └─ no → dual-read; document in EVIDENCE_COVERAGE
├─ primary slug known? → S6 brief or work draft (note if not S6)
├─ focus=security|scope|risk → deepen that axis on full baseline
├─ brief mode? → summary + EVIDENCE_COVERAGE only (still gated)
├─ Draft (requirement_risk + presentation)
│       └─ with KEY → .jira_attachments/<KEY>/risk_draft.md
└─ Gate loop
        ├─ validate_requirement_risk_report.py [--brief] [--evidence-dir …]
        ├─ fail → fix failures only → retry (≤3)
        └─ pass → deliver in chat
```

## Responsibility

| Layer | Agent | Script |
|-------|-------|--------|
| Evidence | Which briefs / dual-root | Fetch issue & attachments |
| Generate | Classify/severity + presentation | Does **not** write prose |
| Gate | Fix from report | `validate_requirement_risk_report.py` |
| Semantic correctness | Agent + human reader | No MUST adjudication |

## Gate rules

1. Full and `brief` modes must pass the validator before delivery.
2. Counts in summary/AUDIT_COUNTS must match `#### R-00N · …` titles.
3. Must include **Scope**; full mode ≥1 `R-00N` block; `brief` needs `EVIDENCE_COVERAGE`.
4. On fail, fix only reported issues; do not skip the gate.
5. Standards: `requirement_risk.md` + presentation; scripts verify only.
6. Never write `curated/` or run `domain_check distill`; `risk_draft.md` is for gating only.

## Handoff to `@ticket-splitter`

- “Must decide first” `R-00N` items are preferred splitter inputs.
- Do not wait for human confirm on the risk report before splitting.

## Presentation & domain library

- [`references/presentation.md`](references/presentation.md) · P10: [`../_shared/presentation-p10.md`](../_shared/presentation-p10.md)
- [`../../contracts/jira-issue-domain-knowledge-context.md`](../../contracts/jira-issue-domain-knowledge-context.md)
- Read S6 briefs as **evidence** only; do not write `curated/`.

## Agent checklist

1. Load evidence per `requirement_risk.md` + domain-context contract; fetch attachments if needed; dual-read when roots diverge.
2. Generate substance (`R-00N`, coverage, severities); mark conflicts `[DOMAIN_KNOWLEDGE]`.
3. Apply presentation (+ P10); write `risk_draft.md` when KEY present.
4. Run validator; fix until pass; then deliver in chat (reader locale; often zh-CN for stakeholders).
5. End with copy-paste `@ticket-splitter <same KEY>` (keep `team=` if any), or continue into splitter if already requested.

## Done when

- [ ] Validator exit 0 (or explicitly marked failed)
- [ ] Summary has Scope + must-decide + counts + readiness; counts reconcile
- [ ] `EVIDENCE_COVERAGE` present (full mode also has risk list)
- [ ] Conflicts have source tables; MUST items have suggested owner
- [ ] Splitter handoff present (or already continued)

## Forbidden

- Write `curated/` / run distill check
- Invent facts from the library
- Silently pick Jira vs brief as winner
- Skip gate or wait for confirm unless user asks for ungated draft
- Copy wiki confirm→continue as the risk main flow

## Examples

```text
@requirement-risk DEMO-1 team=demo
→ offline fixture → draft → validate → deliver + handoff splitter

@requirement-risk PROJ-123 brief
→ short draft → validate --brief → summary + EVIDENCE_COVERAGE
```
