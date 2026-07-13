---
name: generate-knowledge-from-wiki
description: >-
  Use when refreshing team domain truth from Confluence before story review.
  Prep: Ingest+Recognize (S1+S2); deliver: Compose S3→S7 for human-confirmed
  module slugs. @generate-knowledge-from-wiki + URL. Partial: Recognize only,
  or @distill-domain-knowledge for Compose.
disable-model-invocation: false
---

# generate-knowledge-from-wiki (Confluence → domain briefs)

**Ingest (S1)** → **Recognize (S2)** → human **confirm** → **Compose (S3→S7)**.

Top coding packs teach agents how to build. This skill adjudicates **domain truth** from Confluence, then feeds `@requirement-risk` / `@ticket-splitter`.

Process terms (first mention): **confirm** = approve module cut lines; **source brief** = S6 adjudicated doc in **source language**; **locale brief** / **brief** = S7 target-locale reader doc; **continue** = resume Compose after confirm. (zh-CN strings for these tokens live in `domain-knowledge/language/deliverable-locale-tokens.json`, cited once here rather than inline throughout.)

**First time with Confluence?** Read [`FIRST-RUN.md`](./FIRST-RUN.md) only — not the full RUNBOOK. Zero-credentials preview: [`../../../WALKTHROUGH.md`](../../../WALKTHROUGH.md).

## When to use / not

| Use | Do not use → instead |
|-----|----------------------|
| Refresh a Confluence subtree; re-run after policy change | Single-ticket risk / split → `@requirement-risk` / `@ticket-splitter` |
| Build domain briefs from wiki | Config only → `@setup-domain-ops` |

## Hard gates (read first)

1. **Strategy-first**: if `s2-domain-profiles.json` `checklist_themes` is empty, or `strategy.md` §2 is still mostly placeholders → **stop**, run `@setup-domain-ops`. Never silently invent industry modules.
2. Default run is **prep only** (S1→S2) then **pause**; do not Compose until checklist rows are marked **confirm**.
3. **No translation in S1–S6**. **S6** = source-language brief (structure + adjudication, same language as S5). **S7** = convert that brief into `defaults.deliverable_locale` (**expression only**, no new semantics).
4. **confirm** means module boundaries are accepted — **not** that briefs already exist.
5. No in-repo HTTP LLM API writing `curated/`.
6. S1 page errors block S2 by default (unless explicit `--allow-partial`).

Full Compose rules → [`references/iron-laws.md`](references/iron-laws.md) (load on demand). Long playbook (by step only): [`RUNBOOK.md`](./RUNBOOK.md) · zh: [`RUNBOOK.zh-CN.md`](./RUNBOOK.zh-CN.md).

## User flow

```text
@setup-domain-ops          # first time: strategy §2 → profiles (+ deliverable_locale)
@generate-knowledge-from-wiki https://your-site.atlassian.net/wiki/spaces/DEMO/overview
```

Follow [`FIRST-RUN.md`](./FIRST-RUN.md): checklist → **confirm** → **continue** → S6 source brief → S7 locale brief.

Offline risk/split without wiki: `@requirement-risk DEMO-1 team=demo` ([`WALKTHROUGH.md`](../../../WALKTHROUGH.md) Path A).

## Agent: five steps

| # | Action |
|---|--------|
| 0 | Ensure profiles non-empty; else `@setup-domain-ops` |
| 1 | `python3 scripts/sync_domain_knowledge_from_confluence.py --url "…"` (S1) |
| 2 | Read `PIPELINE_HANDOFF.json` → root `<R>` |
| 3 | Optional propose → RUNBOOK **§ S2** only → `s2_recognize.py --root-id <R>` → **pause** for confirm |
| 4 | On **continue**: Compose **S3→S5 → S6 (source brief) → S7 (locale brief)** (or `@distill-domain-knowledge`); open RUNBOOK **§ for that step** only |
| 5 | After S7: `python3 scripts/run_distill_gate.py --root-id <R>` |

Do **not** preload RUNBOOK or iron-laws end-to-end.

## Compose language split (S6 / S7)

| Step | What | Language | Typical artifact |
|------|------|----------|------------------|
| **S6** | Adjudicated reader structure from S5 | **Source language** (no translation) | `_deliver/<slug>/<slug>-source-brief.md` |
| **S7** | Locale conversion of S6 only | `team-roots.json` → `defaults.deliverable_locale` (`zh-CN` / `en`) | `…-domain-brief.md` (en); zh-CN filename from `deliverable-locale-tokens.json` |

Risk/split **read the S7 locale brief** by default. If source language already equals `deliverable_locale`, S7 still emits the canonical locale filename (may be near-identical to S6).

## Responsibility (summary)

| | Agent | Script |
|--|-------|--------|
| S1–S2 | Gate semantics, human review | Sync, recognize, closure |
| S3 | Fidelity contract | Extract & index |
| S4–S7 | Domain model + source brief + locale brief | Structural gates; **no** body authorship |

## Forbidden

- Compose S3–S7 without **confirm**
- Translating in S2–S6; skipping S6 and jumping straight to a locale-only draft
- Claiming “briefs done” from work drafts or S6 alone when S7 is required

## Further reading

| Doc | When |
|-----|------|
| [`FIRST-RUN.md`](./FIRST-RUN.md) | **Start here** for Confluence |
| [`RUNBOOK.md`](./RUNBOOK.md) | Open **one step section** while executing |
| [`RUNBOOK.zh-CN.md`](./RUNBOOK.zh-CN.md) | Chinese locale playbook |
| [`references/iron-laws.md`](references/iron-laws.md) | Compose / disputes only |
| [`S1-SYNC-CLI.md`](./S1-SYNC-CLI.md) | S1 flags |

## Next

`@requirement-risk` → `@ticket-splitter` (read **S7** briefs; or offline `DEMO-1`).
