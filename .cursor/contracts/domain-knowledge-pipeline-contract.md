# Domain knowledge · cross-pipeline contract

Chinese locale: [`domain-knowledge-pipeline-contract.zh-CN.md`](./domain-knowledge-pipeline-contract.zh-CN.md).

> **Readers**: Maintainers, Cursor agents.  
> **Scope**: Confluence sync, distill, `curated`, Jira prep, manual upload — **invariants** and **artifact layers**.  
> **Skill-owned steps**: Each skill documents only its own pipeline steps.

| Doc | Role |
|-----|------|
| [`domain-knowledge/strategy.md`](../../domain-knowledge/strategy.md) | Methodology template + fill-in industry (§2); human cut SSOT · [`strategy.zh-CN.md`](../../domain-knowledge/strategy.zh-CN.md) |
| [`domain-knowledge/s2-domain-profiles.json`](../../domain-knowledge/s2-domain-profiles.json) | Machine themes/facets (from strategy; empty shell by default) |
| [`domain-knowledge/distill-quality-bar.md`](../../domain-knowledge/distill-quality-bar.md) | Three-layer baseline · zh: [`distill-quality-bar.zh-CN.md`](../../domain-knowledge/distill-quality-bar.zh-CN.md) |
| [`domain-knowledge/distill-document-skeleton.md`](../../domain-knowledge/distill-document-skeleton.md) | Draft section skeleton · zh: [`distill-document-skeleton.zh-CN.md`](../../domain-knowledge/distill-document-skeleton.zh-CN.md) |
| [`domain-knowledge/language/glossary.md`](../../domain-knowledge/language/glossary.md) | Shared glossary |
| [`domain-knowledge/language/deliverable-locale-tokens.json`](../../domain-knowledge/language/deliverable-locale-tokens.json) | Locale labels / filenames (`deliverable_locale`) |
| [`domain-knowledge/jira/team-roots.json`](../../domain-knowledge/jira/team-roots.json) | v3: `libraries` (space/`root_id`/deliver) + `teams` (board + mounts) |

---

## 1. Artifact layers (repo paths)

| Layer | Path | Writer | External commitment? |
|-------|------|--------|----------------------|
| Extract | `extracted/by-root/<root>/` | Scripts | No (intermediate) |
| Materialized source | `materialized/by-root/<root>/` | Scripts | No (faithful sync; often English) |
| Per-theme aggregate | `curated/.../_aggregate/<slug>/` | Cursor (S3) | No |
| Work draft | `.../_deliver/<slug>/*-work-draft.md` | Cursor (S4/S5) | No |
| Source-language brief | `.../_deliver/<slug>/*-source-brief.md` | Cursor (**S6**) | No (intermediate adjudication) |
| **Locale brief** | `.../_deliver/<slug>/*-domain-brief.md` (zh-CN: locale-brief suffix) | Cursor (**S7**) | **Yes** |
| Jira side path | `.../jira/by-theme/<theme>/` | Scripts + Cursor | Indexes / attribution; merge into briefs via Compose |
| Glossary | `domain-knowledge/language/glossary.md` | Scripts (after S7) + humans | Whole library |

**Authoritative source**: Confluence pages. To change business facts → edit Confluence → re-sync. **Do not** treat long-lived hand edits to `materialized/` as authority.

---

## 2. Enumeration root vs on-disk root (Confluence sync)

| Concept | Meaning |
|---------|---------|
| **Enumeration root** | Page ID from the pasted URL (optional ancestor promotion). Decides **which subtree this run pulls**. |
| **On-disk root** | `<ID>` in `by-root/<ID>/`. Shared by `extracted/`, `materialized/`, `curated/`. |

- **Space overview**: enumeration root ≈ on-disk root ≈ space home ID (full-library refresh).
- **Child page + default reuse**: enumeration root = child; on-disk root often = existing team library ID. Lookup order: (1) **local** `extracted/.../pages/<childId>.md` (no Confluence); (2) if miss, Confluence **ancestors** then local match; (3) else new `by-root/<childId>/`. Do not create a parallel root when (1) or (2) hits.
- Disable reuse: `--no-reuse-existing-by-root` or `CONFLUENCE_REUSE_EXISTING_BY_ROOT=0` → on-disk root = enumeration root.

**`PIPELINE_HANDOFF.json`** (`extracted/by-root/<on-disk root>/`): `root_page_id` = on-disk root; if `enumeration_root_page_id` is set it may differ. Distill and gate scripts **always use the on-disk root**.

---

## 3. Wiki pipeline (`@generate-knowledge-from-wiki`)

**Narrative stages**: **Ingest** (S1) → **Recognize** (S2) → **Compose** (S3→S7). **S1–S7** remain operational step IDs (gates, paths). **Prep** = Ingest + Recognize; **deliver** = Compose.

| Stage | Step | Artifacts | Actor |
|-------|------|-----------|-------|
| Ingest | S1 | `extracted/`, `materialized/` | `sync_domain_knowledge_from_confluence.py` |
| Recognize | S2 | Checklist, closure | Cursor |
| Compose | S3–S7 | `_aggregate/`, work draft, source brief, locale brief | Cursor |

**Sole runbook** (stages + S1–S7; language policy in RUNBOOK):

**[`generate-knowledge-from-wiki/RUNBOOK.md`](../skills/generate-knowledge-from-wiki/RUNBOOK.md)**

- User entry: [`generate-knowledge-from-wiki/SKILL.md`](../skills/generate-knowledge-from-wiki/SKILL.md)
- Recognize / Compose only (no Ingest): [`distill-domain-knowledge/SKILL.md`](../skills/distill-domain-knowledge/SKILL.md) → still read RUNBOOK

**Invariants (summary)**: no external HTTP LLM for curated drafts; extract defaults to **no** full-document translation (locale language only at **S7**); same-turn `@generate-knowledge-from-wiki` **must** run Ingest → Recognize → Compose (S1→S7), not stop at `materialized/`.

---

## 4. Jira pipeline (`@add-knowledge-from-jira`)

**Sole runbook**: [`add-knowledge-from-jira/RUNBOOK.md`](../skills/add-knowledge-from-jira/RUNBOOK.md) · **Recognize + Compose** shared with [`generate-knowledge-from-wiki/RUNBOOK.md`](../skills/generate-knowledge-from-wiki/RUNBOOK.md)

**Narrative**: **Ingest → Classify → Recognize** (shared) → **Compose** (shared Wiki S3→S7). Old Extract / Integrate paths are removed.

| Stage | Actor | Artifacts |
|-------|-------|-----------|
| Ingest | `run_jira_ingest.py` | `jira/raw/`, `jira/materialized/` |
| Classify | `attribute.py` + `read_business.py` + Cursor review | `attribution/`, theme indexes |
| Recognize | Cursor (Wiki RUNBOOK) | Shared checklist, closure |
| Compose | Cursor (Wiki RUNBOOK S3–S7) | `_aggregate/`, work draft, source brief, locale brief |

Orchestrator: `scripts/run_jira_knowledge.py` (**script prep** only: Ingest+Classify).

- **Script prep** = Ingest + Classify + `domain_check jira --full-raw` → stop; **full prep** also needs Cursor Recognize (Wiki RUNBOOK · S2)
- **Done (machine)**: `domain_check jira --full-raw` for prep; `domain_check distill` for Compose brief quality
- **Invariant**: ticket coverage ≠ done; confirmed themes must absorb Jira business evidence in `_aggregate/`, work drafts, and briefs
- **Proposition `primary`** = confirmed **slug**, not `requirements` / `gateway` sinks

Team config: `team-roots.json` · path SSOT: `scripts/teams/registry.py`.

---

## 5. Teams / `root_id` (config-driven · any N)

SSOT: `domain-knowledge/jira/team-roots.json` (template: `team-roots.example.json`).

- As many teams as keys in `teams`; keys are yours (`demo`, `orders`, `mobile`, …).
- Optional `defaults.default_team` when CLI omits `--team`.
- This repo ships one `demo` team and an empty `checklist_themes` shell; fill `strategy.md` §2 and derive profiles before Recognize. Add more keys under `teams{}` for more product lines.

```bash
python3 -c "from teams.registry import load_team_roots; print(list(load_team_roots()))"
```

---

## 6. Steady-state user duties (all three pipelines)

1. Start: `@generate-knowledge-from-wiki` + URL, or `@add-knowledge-from-jira` + `team`, or `@distill-domain-knowledge` alone (RUNBOOK S2–S7).
2. **Do not** assume you must open a terminal (agent runs commands); credentials in `.env`: `ATLASSIAN_EMAIL`, `ATLASSIAN_API_TOKEN`.
3. Spot-check `_deliver/` briefs; fix business errors in **Confluence**, then re-run.
4. Optional: after gates pass, humans upload to Confluence.

---

## 7. Script SSOT (maintainers)

| Use | Entry |
|-----|-------|
| Team / brief paths | `scripts/teams/registry.py` |
| Confluence sync | `scripts/sync_domain_knowledge_from_confluence.py` (`scripts/wiki/sync/`) |
| Unified gates | `scripts/domain_check.py distill\|jira\|all` |
| Jira orchestration | `scripts/run_jira_knowledge.py` · Ingest: `scripts/run_jira_ingest.py` |
| Confluence upload | Manual |
| Historical migrate | No retained archive scripts; delete after one-shot moves |

Reader entry: repo root [`TEAM_KNOWLEDGE_BASE.md`](../../TEAM_KNOWLEDGE_BASE.md).

---

## 8. Single-ticket Jira helper skills (not the domain-library pipeline)

Parallel to §3–§4; **do not** write `curated/`:

| Skill | Role |
|-------|------|
| `@requirement-risk` | Single-ticket risk visibility (chat deliverable; rule: `requirement_risk`) |
| `@ticket-splitter` | Single-ticket split (rule: `ticket_system`) |
| `@ticket-test-design` | Single-ticket test design / Done proof pack (rule: `ticket_test_design`) |
| `scripts/jira/attachments/fetch_jira_attachments.py` | REST drop under `.jira_attachments/<KEY>/` when MCP lacks attachments |

**Domain-library linkage**: these skills **default-read** wiki/jira disk artifacts (`_deliver`, attribution YAML, `by-theme` indexes, etc.) — see [`jira-issue-domain-knowledge-context.md`](jira-issue-domain-knowledge-context.md). They **do not** replace §3–§4 and **do not** write `curated/`.

Index: [`.cursor/skills/README.md`](../skills/README.md). Credentials may share `ATLASSIAN_*` with §7.
