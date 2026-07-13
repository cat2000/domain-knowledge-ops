# Jira → domain knowledge (business-detail evidence)

Chinese locale: [`README.zh-CN.md`](./README.zh-CN.md).

Jira is a first-class source of business detail: AC, comments, status transitions, thresholds, and last-wins decisions enter the same `curated/by-root/<root>/` Compose mainline as Confluence.

**Agent playbook**: [`.cursor/skills/add-knowledge-from-jira/RUNBOOK.md`](../../.cursor/skills/add-knowledge-from-jira/RUNBOOK.md)  
**User entry**: [`.cursor/skills/add-knowledge-from-jira/SKILL.md`](../../.cursor/skills/add-knowledge-from-jira/SKILL.md)  
**Ingest flags**: [`.cursor/skills/add-knowledge-from-jira/INGEST-CLI.md`](../../.cursor/skills/add-knowledge-from-jira/INGEST-CLI.md)  
**Classify flags**: [`.cursor/skills/add-knowledge-from-jira/CLASSIFY-CLI.md`](../../.cursor/skills/add-knowledge-from-jira/CLASSIFY-CLI.md)

**Constraints**: no external LLM API. Ingest/Classify are deterministic prep; Recognize/Compose are Cursor semantic judgment. Legacy Extract/Integrate are removed.

**First-principles attribution**: [first-principles-attribution.md](first-principles-attribution.md)  
**Layers & history**: [pipeline-design.md](pipeline-design.md)  
**Team configs**: `teams/<team>.json` (shipped: [`teams/demo.json`](teams/demo.json))

## Pipeline (Jira prep + unified Compose)

| Stage | Who | Artifacts |
|-------|-----|-----------|
| **Ingest** | `run_jira_ingest.py` | `jira/raw/`, `jira/materialized/` |
| **Classify** | `attribute.py` + `read_business.py` + Cursor | `attribution/`, theme indexes |
| **Recognize** | Cursor ([Wiki RUNBOOK](../../.cursor/skills/generate-knowledge-from-wiki/RUNBOOK.md)) | Map Jira attribution onto shared `DOMAIN_MODULE_CHECKLIST.md` + closure |
| **Compose** | Cursor (unified **S3→S7**) | `_aggregate/`, work drafts, S6/S7 briefs; S3 admits Jira business evidence |

Details: **[`add-knowledge-from-jira/RUNBOOK.md`](../../.cursor/skills/add-knowledge-from-jira/RUNBOOK.md)**.

## Teams & config

Boards and `root_id` live in **[`team-roots.json`](team-roots.json)** via **`scripts/teams/registry.py`**.

**Ingest**:

| Command | Output |
|---------|--------|
| `run_jira_ingest.py --mode sprint --sprint-id <id>` | `jira/raw/<KEY>.json` |
| `run_jira_ingest.py --mode history --until-complete` | Oldest→current sprint pull + `sync-state.json` |
| Optional materialize | `jira/materialized/<KEY>.md` |

Sprint queue: `jira/lib/jira_sprints.py` → `sprints-closed.json`.

## Directory layout

```text
domain-knowledge/curated/by-root/<root_id>/jira/
  sync-state.json
  batch-manifest.json
  JIRA_PIPELINE_HANDOFF.json
  raw/<KEY>.json
  materialized/<KEY>.md
  attribution/<KEY>.yaml
  _ticket_attribution.json
  by-theme/<theme>/
    full-KEY-index.md, gap-scan.md   # Classify indexes (locale names via deliverable_locale tokens)
```

## Orchestrator (`run_jira_knowledge.py`)

| Invocation | Meaning |
|------------|---------|
| (no flag) | **Prep**: board history through current sprint + Classify + gate → **stop** |
| `--sprint-id <id>` | **Prep**: that sprint only + Classify + gate → **stop** |

## Examples

```text
@add-knowledge-from-jira team=demo mode=history
@add-knowledge-from-jira board-id=1 mode=history
@add-knowledge-from-jira team=demo mode=sprint sprint-id=1726
@add-knowledge-from-jira team=demo mode=compose
```

## Recommended commands

```bash
# Prep
python3 scripts/run_jira_knowledge.py --team demo
python3 scripts/run_jira_knowledge.py --team demo --sprint-id 1726

# Compose: after checklist Status = confirmed, run wiki RUNBOOK Compose (S3→S7)

# Gates
python3 scripts/domain_check.py jira --team demo --full-raw
python3 scripts/domain_check.py distill --root-id 100001
```

## Quality

- Provenance alongside Confluence: **Jira KEY + Confluence links**.
- Cross-ticket conflicts: later **`effective_at` wins**; unresolved → open items.
- **S3 admission**: `distill_tier=proposition_core/platform_variant`.
- **Recognize**: do not re-recognize from `materialized/` files; use `attribution/*.yaml` fields into the shared confirm gate.
- **Done**: confirmed themes show Jira detail merged in `_aggregate/` / drafts / S7 briefs — **not** ticket coverage %.

## Hierarchy (`parent`)

Besides **issuelinks**, many teams use Jira **`fields.parent`**:

| Mechanism | Use |
|-----------|-----|
| **`parent` / `parent_key`** | Child → immediate parent |
| **`parent_chain`** | Optional `--resolve-parent-chain` |
| **`_parent_index.json`** | Batch raw summary |

**Classify**: prefer parent summary when present; `themes` may inherit; child comments may override.
