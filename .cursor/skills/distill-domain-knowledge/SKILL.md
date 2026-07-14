---
name: distill-domain-knowledge
description: >-
  Advanced: Compose S3→S7 or redo Recognize/S2 when materialized/ already
  exists (no re-sync). Default resume after wiki prep is saying continue in
  the same thread — use this skill for partial steps or a fresh Compose
  session. Full pipeline: @generate-knowledge-from-wiki.
disable-model-invocation: false
---

# distill-domain-knowledge (Recognize or Compose — no Ingest)

**Advanced resume.** After wiki prep, the default is: human **confirm** → say **continue** (same thread as `@generate-knowledge-from-wiki`). Use this skill when you need Compose/Recognize **without** re-running Ingest, or a **single-step** / fresh-session resume.

Playbook: [`generate-knowledge-from-wiki/RUNBOOK.md`](../generate-knowledge-from-wiki/RUNBOOK.md) (three stages; steps **S1–S7**). Chinese locale: [`RUNBOOK.zh-CN.md`](../generate-knowledge-from-wiki/RUNBOOK.zh-CN.md).

**confirm** / **continue** — same meaning as wiki skill. (zh-CN strings for these tokens: `domain-knowledge/language/deliverable-locale-tokens.json`.)

## When to @

| Scenario | Do |
|----------|-----|
| Just finished wiki prep (same thread) | Wait for **confirm**, then say **continue** — **do not** require `@distill` |
| Checklist already **confirm**; new chat / no wiki thread | `@distill-domain-knowledge <R>` → Compose **S3→S7** |
| Re-run Recognize only | `@distill-domain-knowledge <R>` + “S2” |
| One theme sub-step | `@distill-domain-knowledge <R>` + `theme <slug> S3` / `S4` / `S5` / `S6` / `S7` |

## Agent

1. Open **RUNBOOK** and `domain-knowledge/distill-authoring-contract.md`; run the requested range (S2: `python3 scripts/distill/s2_recognize.py --root-id <R>`).
2. **S3 / S4 / S5 / S6**: do not translate. **S6** = source brief (`*-source-brief.md`). **S7** = locale / reader brief (`*-domain-brief.md` for en; zh-CN filename from `deliverable-locale-tokens.json`).
3. **Keep industry axes**: remount product-surface evidence per [`industry-axis-remount.md`](../generate-knowledge-from-wiki/references/industry-axis-remount.md); do not recreate Mall/Hui/Gateway modules by default.
4. **S2 contract**: require `S2_DECISION_LEDGER.json` + `S2_REVIEW_DECISIONS.json`; human entry is `DOMAIN_MODULE_CHECKLIST.md`. After S2: `tagging_acceptance.py --root-id <R>` before confirm.
5. After S3: `tagging_acceptance.py --root-id <R> --after-s3`. After S7: `--after-s7 --strict` (zero-rule fake coverage = FAIL → revert confirm).
6. `domain_check distill`: after **S2** (coverage); after **S7** (full).
