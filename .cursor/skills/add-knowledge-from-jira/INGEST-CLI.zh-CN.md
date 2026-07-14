# add-knowledge-from-jira · Ingest CLI（参数 / 排障）

> English SSOT: [`INGEST-CLI.md`](./INGEST-CLI.md).
>
> **阶段**：**Ingest** · **剧本**：[`RUNBOOK.md`](./RUNBOOK.md) · **入口**：[`SKILL.md`](./SKILL.md)  
> **编排**：`scripts/run_jira_knowledge.py` · **入口脚本**：`scripts/run_jira_ingest.py`

## 两种拉取策略（仅此两种）

| 策略 | CLI | 含义 |
|------|-----|------|
| **指定 Sprint** | `--mode sprint --sprint-id <id>` | 该 Sprint 全部 issue（含 comments） |
| **Board 历史拉满** | `--mode history --until-complete` | 从最早 Sprint 拉到当前（含当前） |

**SSOT**：归因读 `raw/` + `attribution/`；S3 准入读 S2 closure；`materialized/` 供阅读（非权威）。

团队 / board / `root_id`：[`team-roots.json`](../../../domain-knowledge/jira/team-roots.json) · `scripts/teams/registry.py`（用 team key 或 board id 解析，**不要**在 skill 里写死租户等价表）。

## 编排顺序

`run_jira_ingest.py`（默认 **仅 fetch**）：

1. `jira/steps/fetch.py` → `jira/raw/<KEY>.json`
2. 可选 `jira/steps/materialize.py`（`--materialize`）

```bash
python3 scripts/jira/steps/fetch.py --team demo --mode sprint --sprint-id 1726
python3 scripts/jira/steps/materialize.py --team demo
```

## 命令速查

```bash
python3 scripts/run_jira_ingest.py --team demo --mode sprint --sprint-id 1726
python3 scripts/run_jira_ingest.py --team demo --mode history --until-complete
python3 scripts/run_jira_ingest.py --team demo --mode history --until-complete --materialize
```

## 故障排查

| 现象 | 处理 |
|------|------|
| `HTTP 401/403` | `.env` 凭证与 Jira 权限 |
| `Sprint id … not in queue` | `--refresh-sprints` 或检查 `team-roots.json` |
| `no issues returned` | 空 Sprint / JQL |
