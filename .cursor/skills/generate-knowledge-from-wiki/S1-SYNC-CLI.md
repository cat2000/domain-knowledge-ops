# generate-knowledge-from-wiki · S1 sync CLI

> Playbook: [`RUNBOOK.md`](./RUNBOOK.md) · Entry: [`SKILL.md`](./SKILL.md) · Chinese: [`S1-SYNC-CLI.zh-CN.md`](./S1-SYNC-CLI.zh-CN.md)

## Link resolution

Paste a **Confluence URL or numeric ID** → enumeration root (`/pages/<id>/`, `homepageId=`, space overview via REST homepage, long numeric IDs in body).

- **Default**: pasted page = enum root → full descendants → `extracted/by-root/<ID>/`, `materialized/by-root/<ID>/` (disk root may differ if reuse applies; see pipeline contract §2). Reuse order: **local page hit first**, then Confluence ancestors if miss.
- **Team-wide library**: paste Space overview / homepage — do not treat product subgroup pages as the default canonical root.
- **Ancestor promotion** (optional): `.env` `CONFLUENCE_CANONICAL_ROOT_IDS` + `--resolve-canonical-root` or `CONFLUENCE_RESOLVE_CANONICAL_ROOT=1`.

## Orchestrator order

Entry: `scripts/sync_domain_knowledge_from_confluence.py` (prefer `.venv/bin/python3`).

1. `confluence_enumerate_child_pages.py` → `descendants-full.json`  
   - Default `enum-mode=cql` (`--page-size` / `CONFLUENCE_ENUMERATE_PAGE_SIZE`, 1–250)  
   - Optional `--enum-mode bfs` / `CONFLUENCE_ENUM_MODE=bfs`
2. `confluence_extract_pages.py` → `pages/<PAGE_ID>.md` (`kb_outline`)  
   - `--workers` / `CONFLUENCE_EXTRACT_WORKERS`  
   - Attachments off by default; `--attachments page|tree` or advanced env flags
3. Integrity gate: `_last_extract_report.json` with `error_count > 0` stops by default; `--allow-partial` continues with partial handoff
4. `gen_source_coverage.py`
5. `materialize_rules_from_extracted.py` (`--skip-materialize` to skip)  
   - Writes `_materialized_manifest.json`  
   - Purges stale materialized `.md` not in the current source set

**`curated/`**: scripts **do not** write it; Agent writes per RUNBOOK (S2–S6).

## Latency & translation

- Runtime ≈ pages × HTTP + default sleep; attachments/OCR much slower.
- Do **not** enable `CONFLUENCE_KB_TRANSLATE=1` by default. Reader-facing language is only in **S6** briefs.

## Commands

```bash
python3 scripts/sync_domain_knowledge_from_confluence.py --url "<PAGE_URL_OR_ID>"
python3 scripts/sync_domain_knowledge_from_confluence.py --root "<PAGE_ID>"
python3 scripts/sync_domain_knowledge_from_confluence.py --url "..." --attachments tree
python3 scripts/sync_domain_knowledge_from_confluence.py --url "..." --no-reuse-existing-by-root
python3 scripts/sync_domain_knowledge_from_confluence.py --url "..." --enum-mode bfs
python3 scripts/sync_domain_knowledge_from_confluence.py --url "..." --allow-partial
```

## Troubleshooting

| Symptom | Action |
|---------|--------|
| `HTTP 401/403` | Email, API token, space permission |
| `Set ATLASSIAN_EMAIL` | Configure `.env` |
| Slow | Expected for large trees |
| `S1 extract is partial` | Fix extract errors; use `--allow-partial` only when gaps are accepted |

## `kb_outline` is `—`

Page skips rule aggregation; extract body remains under `extracted/.../pages/<PAGE_ID>.md`.
