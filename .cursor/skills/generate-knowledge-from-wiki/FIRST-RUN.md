# generate-knowledge-from-wiki · first run only

> **Newcomers:** use this page + [`SKILL.md`](./SKILL.md).  
> Do **not** read [`RUNBOOK.md`](./RUNBOOK.md) end-to-end on the first pass — open it **by step** when you execute that step.  
> Compose disputes → [`references/iron-laws.md`](./references/iron-laws.md).

Zero-credentials preview (no wiki): [`../../../WALKTHROUGH.md`](../../../WALKTHROUGH.md) Path A / B.

---

## Preconditions

1. Profiles non-empty (`s2-domain-profiles.json` → `checklist_themes`). Else `@setup-domain-ops`.
2. `.env` has Confluence/Jira site credentials.
3. You have a Confluence overview URL for your team root.

## Happy path (prep → pause)

```text
@generate-knowledge-from-wiki https://your-site.atlassian.net/wiki/spaces/…/overview?homepageId=…
```

| # | You / Agent | Stop? |
|---|-------------|-------|
| 1 | S1 sync script runs (`sync_domain_knowledge_from_confluence.py`) | — |
| 2 | Read `PIPELINE_HANDOFF.json` → note `root_id` `<R>` | — |
| 3 | S2 recognize → `DOMAIN_MODULE_CHECKLIST.md` | — |
| 3b | **Tagging acceptance** (required): `python3 scripts/distill/tagging_acceptance.py --root-id <R>` → show report; write `TAGGING_ACCEPTANCE.md` | **Yes — pause** |
| 3c | If team has `board_id` and report says Jira attribution = 0: run `@add-knowledge-from-jira team=<key>` (or ingest+classify), then re-run S2 + tagging acceptance | recommended before confirm |
| 4 | Human sets row **Status** → **confirm** **only for rows the report marks OK** (zero-source rows stay pending) | — |

Default run ends at step 3b–4. That is success for “prep”.

**Do not** tell the user to confirm every checklist row. Industry module cuts are **question axes**; completeness is **bidirectional tagging** (closure + this report), not the strategy table alone.

## Happy path (compose → briefs)

After confirm, say **continue** (optionally name a slug):

| # | Action | Artifact |
|---|--------|----------|
| 5 | Compose S3→S5 (land evidence into **industry axes** — [`references/industry-axis-remount.md`](./references/industry-axis-remount.md)) | work draft |
| 5b | After S3: `python3 scripts/distill/tagging_acceptance.py --root-id <R> --after-s3` | exhaustiveness |
| 6 | **S6** source-language brief | `_deliver/<slug>/<slug>-source-brief.md` |
| 7 | **S7** locale brief (`deliverable_locale`) | `…-domain-brief.md` (en); zh-CN filename from tokens |
| 7b | After S7: `python3 scripts/distill/tagging_acceptance.py --root-id <R> --after-s7 --strict` — fix FAIL rows (zero-rule fake coverage) | write-through gate |
| 8 | `python3 scripts/run_distill_gate.py --root-id <R>` | gate report |

**Low-evidence / zero-rule S7**: if `pages_with_props=0` or S7 has **zero** `### Rule` headings while sources exist → **revert confirm** or rewrite. Do not ship empty core-rules. Insufficiency banner alone is only for intentional placeholders (non-SSOT for risk).

Keep **industry adjudication axes**. Land sources into those axes by business commitment — do not promote source-tree layout into modules, and do not hard-code tenant remount specials.
Then: `@requirement-risk KEY` → `@ticket-splitter KEY` → `@ticket-test-design KEY` (read **S7**).

## When to open the long RUNBOOK

| Need | Open |
|------|------|
| S1 flags / partial sync | [`S1-SYNC-CLI.md`](./S1-SYNC-CLI.md) |
| S2 propose vs recognize details | [`RUNBOOK.md`](./RUNBOOK.md) § S2 |
| S3 proposition fields | RUNBOOK § S3 |
| S4–S7 authoring shape | RUNBOOK § S4–S7 + iron-laws |
| Chinese playbook | [`RUNBOOK.zh-CN.md`](./RUNBOOK.zh-CN.md) |

## Do not on first run

- Preload all iron laws
- Compose without **confirm**
- Confirm zero-source rows, zero-rule S7 fake coverage, or claim “coverage done” from the industry module table alone
- Skip tagging acceptance / ignore Jira=0 when a board is configured
- Recreating modules from wiki/Jira filing layout instead of landing into strategy axes
- Hard-coding tenant product→slug remount tables into the pack
- Inventing modules when profiles are empty
- Expecting Path A offline fixture to replace Confluence sync
