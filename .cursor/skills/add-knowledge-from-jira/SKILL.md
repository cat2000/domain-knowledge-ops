---
name: add-knowledge-from-jira
description: >-
  @add-knowledge-from-jira + team/board-id or sprint-id: Jira Ingest→Classify,
  shared Recognize, unified Compose S3→S7. Jira tickets are primary
  business-rule evidence, not post-S7 appendices. Default = prep
  (Ingest+Classify). No external OpenAI API.
disable-model-invocation: false
---

# add-knowledge-from-jira (Jira → business-rule evidence)

Pipeline: **Ingest** → **Classify** → **Recognize** (shared **confirm** with wiki) → **Compose** (unified **S3→S7**). AC, comments, and last-wins decisions are first-class domain evidence — they enter the S3/S4/S5 mainline, not a post-brief patch.

**confirm** authorizes Compose; it is **not** “briefs already done”. (zh-CN strings for these tokens: `domain-knowledge/language/deliverable-locale-tokens.json`.)

Compose language (same as wiki): **S6** = source-language brief; **S7** = convert to `deliverable_locale` (expression only).

## When to use

- Fold sprint/history ticket rules, AC, and comment decisions into the same domain library
- **Not** for single-ticket risk/split/test-design → `@requirement-risk` / `@ticket-splitter` / `@ticket-test-design`

## Prep vs Compose (stop boundaries)

| Label | Contains | Who | Stops at |
|-------|----------|-----|----------|
| **Script prep** | Ingest + Classify | `run_jira_knowledge.py` (no flag = board history; `--sprint-id` = one sprint) | After `domain_check jira --full-raw` |
| **Full prep** | Script prep + Cursor **Recognize** | Agent (wiki RUNBOOK · S2) | Checklist + closure ready → wait for **confirm** |
| **Compose** | Unified S3→S7 | Agent + wiki RUNBOOK | Only **confirm**ed themes; S3 includes eligible Jira materializations |

## User `mode=` → CLI

| User `mode=` | Agent runs |
|--------------|------------|
| `history` + `team=<t>` | `python3 scripts/run_jira_knowledge.py --team <t>` (board history through current sprint) + Classify |
| `history` + `board-id=<id>` | Resolve team via `team-roots.json`, then same as history |
| `sprint` + `sprint-id=<id>` | `run_jira_knowledge.py --team <resolved> --sprint-id <id>` + Classify |
| (default / prep) | `history` if team/board given; `sprint` if sprint-id given |
| `compose` / `continue` | Wiki RUNBOOK Compose (**S3→S7**); S3 reads Confluence **and** Jira evidence |
| `distill` / `reconcile` / `full` | **Removed** — refuse; use prep → Recognize → Compose |

## Hard rules

1. **Ingest** (script): `jira/raw/` — [`INGEST-CLI.md`](./INGEST-CLI.md)
2. **Classify** (script): `attribution/` + theme indexes — [`CLASSIFY-CLI.md`](./CLASSIFY-CLI.md)
3. Ticket count ≠ done: Classify coverage is **not** pipeline completion ([`pipeline-design.md`](../../../domain-knowledge/jira/pipeline-design.md))
4. Jira is not an appendix: `distill_tier=proposition_core/platform_variant` tickets enter S3 proposition candidates
5. Recognize shares `DOMAIN_MODULE_CHECKLIST.md` with wiki; **confirm** authorizes Compose
6. Compose follows [`generate-knowledge-from-wiki/RUNBOOK.md`](../generate-knowledge-from-wiki/RUNBOOK.md) (**S6 source brief → S7 locale brief**)
7. Legacy Extract/Integrate paths are deleted — do not revive post-S7 Jira patches
8. `primary` / `themes[]` = confirmed slugs; `gateway` / `requirements` are sink buckets, **not** domains
9. Source of truth is Jira; do not treat hand-edited `jira/materialized/` as authority
10. No in-repo HTTP LLM API
11. **No translation in S1–S6**; locale conversion only in **S7**

## User examples

```text
@add-knowledge-from-jira team=demo mode=history
@add-knowledge-from-jira board-id=1 mode=history
@add-knowledge-from-jira team=demo mode=sprint sprint-id=1726
```

Review checklist → **confirm** → **continue** → verify aggregates/work drafts/**S6+S7 briefs** include Jira rules.

## Agent checklist

| # | Action |
|---|--------|
| 1 | **Ingest**: `run_jira_ingest.py` or `run_jira_knowledge.py` ([`INGEST-CLI.md`](./INGEST-CLI.md)) |
| 2 | Read `JIRA_PIPELINE_HANDOFF.json` → `curated/by-root/<R>/` |
| 3 | **Classify** ([`CLASSIFY-CLI.md`](./CLASSIFY-CLI.md)) → **Recognize** → pause at full prep |
| 4 | On **continue** (confirm rows only): Compose **S3→S7**; proposition lists should show `source_system: jira` |
| 5 | After Compose: `domain_check distill --root-id <R>`; optionally `domain_check jira --full-raw` |

## Forbidden

- Report “pipeline done” because N tickets have attribution
- Claim Jira rules merged from the gap-scan index (`by-theme/<team>/` output of `read_business.py`) alone
- Compose without **confirm**
- Promote `gateway` / `requirements` to confirmed checklist rows
- Run deleted legacy scripts or post-S7 patches
- Skip S6 and write only a translated S7 file

## Further reading

| Doc | Purpose |
|-----|---------|
| [`RUNBOOK.md`](./RUNBOOK.md) | Jira stages + shared layers |
| [`RUNBOOK.zh-CN.md`](./RUNBOOK.zh-CN.md) | Chinese locale playbook |
| [`INGEST-CLI.md`](./INGEST-CLI.md) / [`CLASSIFY-CLI.md`](./CLASSIFY-CLI.md) | Script flags & gates |
| [`generate-knowledge-from-wiki/RUNBOOK.md`](../generate-knowledge-from-wiki/RUNBOOK.md) | Shared Recognize + Compose |
| [`../../contracts/domain-knowledge-pipeline-contract.md`](../../contracts/domain-knowledge-pipeline-contract.md) | Artifact layers |

## Next

`@requirement-risk` → `@ticket-splitter` → `@ticket-test-design` (read **S7** Compose briefs).
