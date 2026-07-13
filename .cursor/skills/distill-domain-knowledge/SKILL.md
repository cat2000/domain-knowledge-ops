---
name: distill-domain-knowledge
description: >-
  Use when materialized/ already exists: RUNBOOK Compose S3→S7 (or redo
  Recognize/S2) without re-sync. Say continue after human confirm. Full
  pipeline: @generate-knowledge-from-wiki.
disable-model-invocation: false
---

# distill-domain-knowledge (Recognize or Compose — no Ingest)

Playbook: [`generate-knowledge-from-wiki/RUNBOOK.md`](../generate-knowledge-from-wiki/RUNBOOK.md) (three stages; steps **S1–S7**). Chinese locale: [`RUNBOOK.zh-CN.md`](../generate-knowledge-from-wiki/RUNBOOK.zh-CN.md).

**confirm** / **continue** — same meaning as wiki skill. (zh-CN strings for these tokens: `domain-knowledge/language/deliverable-locale-tokens.json`.)

## When to @

| Scenario | Do |
|----------|-----|
| Just finished wiki prep | Wait for **confirm**, then **continue** |
| Re-run Recognize | `@distill-domain-knowledge <R>` + “S2” |
| Checklist already **confirm** | **continue** → **Compose (S3→S7)** |
| One theme sub-step | `+ theme <slug> S3` / `S4` / `S5` / `S6` / `S7` |

## Agent

1. Open **RUNBOOK** and `domain-knowledge/distill-authoring-contract.md`; run the requested range (S2: `python3 scripts/distill/s2_recognize.py --root-id <R>`).
2. **S3 / S4 / S5 / S6**: do not translate. **S6** = source-language brief (`*-source-brief.md`). **S7** = locale conversion to `deliverable_locale` (`*-domain-brief.md` for en; zh-CN filename from `deliverable-locale-tokens.json`).
3. **S2 contract**: require `S2_DECISION_LEDGER.json` + `S2_REVIEW_DECISIONS.json`; human entry is `DOMAIN_MODULE_CHECKLIST.md`.
4. `domain_check distill`: after **S2** (coverage); after **S7** (full).
