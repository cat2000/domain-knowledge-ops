# Demo samples

Static examples of what `@requirement-risk` and `@ticket-splitter` produce for the shipped offline fixture. **Not** live agent output — use these to compare structure and grounding after you run Path A in [`WALKTHROUGH.md`](../../WALKTHROUGH.md).

## Fixture inputs

| Artifact | Path |
|----------|------|
| Story | [`domain-knowledge/fixtures/offline-demo/jira/DEMO-1.md`](../../domain-knowledge/fixtures/offline-demo/jira/DEMO-1.md) |
| Attribution | [`domain-knowledge/fixtures/offline-demo/jira/DEMO-1.attribution.yaml`](../../domain-knowledge/fixtures/offline-demo/jira/DEMO-1.attribution.yaml) |
| S7 locale brief (`ordering`) | [`domain-knowledge/fixtures/offline-demo/curated/by-root/100001/_deliver/ordering/ordering-domain-brief.md`](../../domain-knowledge/fixtures/offline-demo/curated/by-root/100001/_deliver/ordering/ordering-domain-brief.md) |

Invoke in Cursor (repo root open, no `.env`):

```text
@requirement-risk DEMO-1 team=demo
@ticket-splitter DEMO-1 team=demo
```

Add `brief` for short mode on either skill.

## Sample outputs

| Sample | Skill | Notes |
|--------|-------|-------|
| [`requirement-risk-DEMO-1.sample.md`](./requirement-risk-DEMO-1.sample.md) | `@requirement-risk` | Refinement depth; MUST items on open-order amend + quote validity |
| [`ticket-splitter-DEMO-1.sample.md`](./ticket-splitter-DEMO-1.sample.md) | `@ticket-splitter` | INVEST slices with `scope` / `done_when` |

Samples are grounded in **DEMO-1** acceptance criteria and the **ordering** brief rule clusters (Open + valid quote, expired quote, shipped/cancelled, partial ship). They do not invent product facts beyond those sources.

## Validation

Agent output must pass the project validate scripts for each skill (see skill `SKILL.md` and `.cursor/rules/`). If your run diverges in **substance** but passes gates, compare evidence tags (`[DOMAIN_KNOWLEDGE]`) and MUST counts against these samples.
