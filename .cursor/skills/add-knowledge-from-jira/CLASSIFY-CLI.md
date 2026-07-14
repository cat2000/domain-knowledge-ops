# add-knowledge-from-jira · Classify CLI

> Stage: **Classify** · Playbook: [`RUNBOOK.md`](./RUNBOOK.md) · Skill: [`SKILL.md`](./SKILL.md)  
> Prerequisite: [`INGEST-CLI.md`](./INGEST-CLI.md) (`jira/raw/` must exist) · Chinese: [`CLASSIFY-CLI.zh-CN.md`](./CLASSIFY-CLI.zh-CN.md)

**Classify ≠ Recognize**: this stage is ticket triage (`attribution/`, theme **indexes**). Proposition-level recognize + human **confirm** is wiki RUNBOOK · S2.

## Orchestration vs single step

| Mode | Command | When |
|------|---------|------|
| **Recommended prep** | `python3 scripts/run_jira_knowledge.py --team <t>` | History through current sprint + Classify + `--full-raw` gate → **stop** |
| **Classify only** | Ensure `raw/` exists, then attribute + read_business + check | Ingest already done |
| **Skip Classify** | `run_jira_knowledge.py --skip-attribute` | Maintainer debug only |

Internal Classify segment:

1. `jira/steps/attribute.py`
2. `jira/steps/read_business.py`
3. `domain_check.py jira --team <t> --full-raw`

## attribute

```bash
python3 scripts/jira/steps/attribute.py --team demo
python3 scripts/jira/steps/attribute.py --team demo --keys PROJ-1,PROJ-2
python3 scripts/jira/steps/attribute.py --team demo --no-preserve-cursor-reviewed
```

| Flag | Meaning |
|------|---------|
| `--team` | Required team key from `team-roots.json` |
| `--keys` | Comma KEY list; omit = all `raw/*.json` |
| `--no-preserve-cursor-reviewed` | Overwrite `cursor_review` / high-confidence YAML (**careful**) |

## read_business / gates

```bash
python3 scripts/jira/steps/read_business.py --team demo
python3 scripts/domain_check.py jira --team demo --full-raw
```

Ticket count with attribution ≠ pipeline done. Proceed to shared Recognize after Classify.

Full prep notes: Chinese locale [`CLASSIFY-CLI.zh-CN.md`](./CLASSIFY-CLI.zh-CN.md) mirrors this file (demo examples only).
