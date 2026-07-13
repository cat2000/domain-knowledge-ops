# add-knowledge-from-jira · Ingest CLI

> Stage: **Ingest** · Playbook: [`RUNBOOK.md`](./RUNBOOK.md) · Skill: [`SKILL.md`](./SKILL.md) · Orchestrator: `scripts/run_jira_knowledge.py`  
> Entry: `scripts/run_jira_ingest.py` · Chinese: [`INGEST-CLI.zh-CN.md`](./INGEST-CLI.zh-CN.md)

## Two fetch strategies only

| Strategy | CLI | Meaning |
|----------|-----|---------|
| **Named sprint** | `--mode sprint --sprint-id <id>` | All issues in that sprint (with comments); default does **not** advance `sprint_cursor` |
| **Board history to complete** | `--mode history --until-complete` | Walk `sprints-closed.json` from oldest through current until `sprint_cursor.completed=true` |

**SSOT**: attribution reads `raw/` + `attribution/`; S3 admission uses S2 closure; `materialized/` is faithful md for reading (**not** authority).

Teams / boards / `root_id`: [`team-roots.json`](../../../domain-knowledge/jira/team-roots.json) · `scripts/teams/registry.py`.

## Orchestrator order

`scripts/run_jira_ingest.py` (default **fetch only**):

1. `jira/steps/fetch.py` → `jira/raw/<KEY>.json`
2. Optional `jira/steps/materialize.py` → `jira/materialized/<KEY>.md` (`--materialize`)

`run_jira_knowledge.py` prep: history until-complete fetch → materialize → Classify; with `--sprint-id` only that sprint.

```bash
python3 scripts/jira/steps/fetch.py --team demo --mode sprint --sprint-id 1726
python3 scripts/jira/steps/materialize.py --team demo
```

**`attribution/` / `_deliver/`**: Ingest does **not** write them — see [`CLASSIFY-CLI.md`](./CLASSIFY-CLI.md).

## Sprint queue

- Refresh: `python3 scripts/jira/lib/jira_sprints.py --team <t>`
- Cache: `curated/by-root/<R>/jira/sprints-closed.json`
- Cursor: `sync-state.json` → `sprint_cursor`

## Troubleshooting

| Symptom | Action |
|---------|--------|
| 401/403 | Credentials / project permission |
| Empty fetch | Check `jql_base` / board / sprint id in `team-roots.json` |
| Cursor stuck | Inspect `sprint_cursor`; re-run sprints list |

See Chinese locale file for extended historical notes if needed.
