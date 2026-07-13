# Domain module confirmation page · root `<ROOT_PAGE_ID>`

Copy to: `domain-knowledge/curated/by-root/<ROOT_PAGE_ID>/DOMAIN_MODULE_CHECKLIST.md`, replacing placeholders with the real root id and paths.

**Purpose**: the team **confirms domain module cuts**. Module **Status** = `confirmed` authorizes the agent to run **Compose (S3→S7)**. **confirmed does not mean the locale brief is already done**.

**Layout (narrow-screen friendly)**: one `###` block per theme + field list; humans usually change only **Status**. Do not use wide tables.

Chinese locale: [`DOMAIN_MODULE_CHECKLIST.template.zh-CN.md`](DOMAIN_MODULE_CHECKLIST.template.zh-CN.md).  
Deliverable label map (en ↔ zh-CN): [`language/deliverable-locale-tokens.json`](language/deliverable-locale-tokens.json).  
Agents emit labels for `defaults.deliverable_locale` from that map; this English doc cites **English** labels only.

Status words use English: `confirmed` / `pending`. The zh-CN locale maps these via the token file above.

## Lifecycle (vs Cursor)

**Where themes come from**:

- On each **rescan**, Cursor refreshes blocks from:
  1. Industry ruler: [`strategy.md`](strategy.md) **§2**;
  2. Scan facts: subdirs and representative `.md` under this root's **`materialized/`**.
- **Humans** may add/remove/edit blocks and status/notes/glossary notes; on rescan Cursor **merges**: refresh scan paths, **keep** **`confirmed`** by default (never silently demote to `pending`).

**First / rescan**:

- **First**: if missing, `@generate-knowledge-from-wiki` / `distill-domain-knowledge` creates a draft.
- **Rescan**: incremental merge — refresh paths; on conflict, **human status/notes win** unless the user asks for a reset.

**Ruler**: [`strategy.md`](strategy.md) **§2**.

## Who updates when

- Each wiki **rescan** → **Cursor**: S2 refreshes this page + `_materialization_closure.json`
- After Recognize → **Human**: set accepted modules' **Status** to **`confirmed`**
- After **`continue`** → **Cursor**: Compose **S3→S7** for **confirmed** modules

## Pipeline shape (same as RUNBOOK)

- **S2**: refresh this page; tag all files → `_materialization_closure.json` (no body translation)
- **S3**: confirmed modules only → `_aggregate/<slug>/`
- **S4 / S5**: domain model + work draft → `_deliver/…-work-draft.md`
- **S6**: source-language brief → `…-source-brief.md`
- **S7**: locale brief → `…-domain-brief.md` (`deliverable_locale`)

**No confirmed → no S3–S7**.

## Required themes (short list)

**Status** contains **`confirmed`** only when authorizing Compose.

### (Cursor: start blocks from strategy §2 × scan)

- **Proposition slug**: `example-slug`
- **Strategy axis**: (one-line axis)
- **Scan dirs**: `facet-example/`
- **Main entry**: `_deliver/example-slug/example-slug-work-draft.md`
- **Status**: pending
- **Glossary note**:
- **Note**:

## Provenance & appendix

- Closure JSON: `_materialization_closure.json`
- Non-domain appendix: e.g. `_appendix/non-domain/`

## Gate scripts

- After S2 (recommended): `python3 scripts/distill/coverage.py --root-id <ID>`
- After S7 (full): `python3 scripts/domain_check.py distill --root-id <ID>`

## Incremental themes

(Append more `###` blocks with the same field shape when needed.)
