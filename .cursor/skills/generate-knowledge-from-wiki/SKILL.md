---
name: generate-knowledge-from-wiki
description: >-
  Use when refreshing team domain truth from Confluence before story review.
  Prep: Ingest+Recognize (S1+S2); deliver: Compose S3→S7 for human-confirmed
  module slugs. @generate-knowledge-from-wiki + URL. After confirm, default
  resume is continue; @distill-domain-knowledge is advanced (no re-sync /
  partial step).
disable-model-invocation: false
---

# generate-knowledge-from-wiki (Confluence → domain briefs)

**Ingest (S1)** → **Recognize (S2)** → human **confirm** → **Compose (S3→S7)**.

Top coding packs teach agents how to build. This skill adjudicates **domain truth** from Confluence, then feeds `@requirement-risk` / `@ticket-splitter`.

Process terms (first mention): **confirm** = approve module cut lines; **source brief** = S6 adjudicated doc in **source language**; **locale brief** / **reader brief** = S7 target-locale reader doc; **brief** alone = short mode on risk/split (see `TEAM_KNOWLEDGE_BASE.md`); **continue** = default resume Compose after confirm. (zh-CN strings for process tokens live in `domain-knowledge/language/deliverable-locale-tokens.json`, cited once here rather than inline throughout.)

**First time with Confluence?** Read [`FIRST-RUN.md`](./FIRST-RUN.md) only — not the full RUNBOOK. Zero-credentials preview: [`../../../WALKTHROUGH.md`](../../../WALKTHROUGH.md).

## When to use / not

| Use | Do not use → instead |
|-----|----------------------|
| Refresh a Confluence subtree; re-run after policy change | Single-ticket risk / split → `@requirement-risk` / `@ticket-splitter` |
| Build domain briefs from wiki | Config only → `@setup-domain-ops` |

## Hard gates (read first)

1. **Strategy-first**: if `s2-domain-profiles.json` `checklist_themes` is empty, or `strategy.md` §2 is still mostly placeholders → **stop**, run `@setup-domain-ops`. Never silently invent industry modules.
2. Default run is **prep only** (S1→S2) then **pause**; do not Compose until checklist rows are marked **confirm**.
3. **Tagging acceptance before confirm**: after S2, run `python3 scripts/distill/tagging_acceptance.py --root-id <R>`, show the report, and **do not** ask humans to confirm every row. Zero-source rows stay **pending**. Industry cuts are axes; completeness = remount + closure + report (+ Jira when board exists).
4. **Keep industry axes**: remount product-surface wiki into those axes ([`references/industry-axis-remount.md`](references/industry-axis-remount.md)); do not recreate Mall/Hui/Gateway modules by default.
5. **No translation in S1–S6**. **S6** = source-language brief. **S7** = locale expression only.
6. **confirm** ≠ briefs already exist, and ≠ every corpus rule already written into S7.
7. **Zero-rule fake coverage banned**: after S7, run `tagging_acceptance.py --after-s7 --strict`; confirmed + sources + zero `### 规则` → revert or rewrite.
8. No in-repo HTTP LLM API writing `curated/`.
9. S1 page errors block S2 by default (unless explicit `--allow-partial`).

Full Compose rules → [`references/iron-laws.md`](references/iron-laws.md) (load on demand). Long playbook (by step only): [`RUNBOOK.md`](./RUNBOOK.md) · zh: [`RUNBOOK.zh-CN.md`](./RUNBOOK.zh-CN.md).

## User flow

```text
@setup-domain-ops          # first time: strategy §2 → profiles (+ deliverable_locale)
@generate-knowledge-from-wiki https://your-site.atlassian.net/wiki/spaces/DEMO/overview
# pause: tagging acceptance report → confirm only OK rows
# if board_id set and Jira attribution empty: @add-knowledge-from-jira team=<key> then re-tag
```

Follow [`FIRST-RUN.md`](./FIRST-RUN.md): checklist → **tagging acceptance** → **confirm** → **continue** → S6 → S7 → `--after-s7`.

Offline risk/split without wiki: `@requirement-risk DEMO-1 team=demo` ([`WALKTHROUGH.md`](../../../WALKTHROUGH.md) Path A).

## Agent: five steps

| # | Action |
|---|--------|
| 0 | Ensure profiles non-empty; else `@setup-domain-ops` |
| 1 | `python3 scripts/sync_domain_knowledge_from_confluence.py --url "…"` (S1) |
| 2 | Read `PIPELINE_HANDOFF.json` → root `<R>` |
| 3 | Optional propose → RUNBOOK **§ S2** → `s2_recognize.py` → `tagging_acceptance.py` → **pause** (Jira if board + empty attribution); remount per industry-axis-remount |
| 4 | On **continue**: Compose **S3→S5→S6→S7** with remount write-through; `--after-s3` then `--after-s7 --strict` |
| 5 | After S7: `python3 scripts/run_distill_gate.py --root-id <R>` |

Do **not** preload RUNBOOK or iron-laws end-to-end.

## Compose language split (S6 / S7)

| Step | What | Language | Typical artifact |
|------|------|----------|------------------|
| **S6** | Adjudicated **source brief** from S5 | **Source language** (no translation) | `_deliver/<slug>/<slug>-source-brief.md` |
| **S7** | Locale conversion of S6 only (**reader brief**) | `team-roots.json` → `defaults.deliverable_locale` (`zh-CN` / `en`) | `…-domain-brief.md` (en); zh-CN filename from `deliverable-locale-tokens.json` |

Risk/split **read the S7 locale brief** (reader brief) by default. If source language already equals `deliverable_locale`, S7 still emits the canonical locale filename (may be near-identical to S6).

## Responsibility (summary)

| | Agent | Script |
|--|-------|--------|
| S1–S2 | Gate semantics, human review | Sync, recognize, closure |
| S3 | Fidelity contract | Extract & index |
| S4–S7 | Domain model + source brief + locale brief | Structural gates; **no** body authorship |

## Forbidden

- Compose S3–S7 without **confirm**
- Confirming zero-source modules, or confirmed + sources + **zero** S7 rules (fake coverage)
- Claiming corpus coverage from the industry cut alone
- Recreating Mall/Hui/Gateway/Messaging modules by default instead of remounting into industry axes
- Translating in S2–S6; skipping S6 and jumping straight to a locale-only draft
- Claiming “briefs done” from work drafts or S6 alone when S7 is required
- Shipping low-evidence S7 without an **Evidence insufficiency** banner when intentionally thin (non-SSOT for risk)
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
