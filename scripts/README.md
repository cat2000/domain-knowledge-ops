# scripts · 日常入口与结构

**结构统筹（必读）**：[`ARCHITECTURE.md`](ARCHITECTURE.md)  
**契约**：[`../.cursor/contracts/domain-knowledge-pipeline-contract.md`](../.cursor/contracts/domain-knowledge-pipeline-contract.md)  
**回归测试**：[`../tests/README.md`](../tests/README.md)

## 根目录 CLI

| 文件 | 说明 |
|------|------|
| `sync_domain_knowledge_from_confluence.py` | Wiki **S1** 同步（`extracted/` + `materialized/`） |
| `run_jira_knowledge.py` | Jira 管线主编排 |
| `domain_check.py` | 蒸馏 + Jira 门禁门面 |
| `run_distill_gate.py` | Wiki 定稿一键门禁（S2/S6 一致性 + `domain_check distill`） |
| `_bootstrap.py` | 子进程 `sys.path`（实现 `runtime/`） |
| `_install.py` | 任意深度模块统一 bootstrap（见 `ARCHITECTURE.md`） |

子步骤见各包 **`steps/`**（如 `wiki/steps/extract.py`、`jira/steps/fetch.py`、`distill/coverage.py`）。

## 日常命令

| 用途 | 命令 |
|------|------|
| Confluence 同步（S1） | `python3 scripts/sync_domain_knowledge_from_confluence.py --url …` |
| Jira 备料 | `python3 scripts/run_jira_knowledge.py --team cma\|bc\|wc` |
| 统一门禁 | `python3 scripts/domain_check.py distill\|jira\|all` |
| Wiki 定稿门禁 | `python3 scripts/run_distill_gate.py --root-id <R>`（通过后自动更新 `glossary.md`） |
| 术语表更新 | `python3 scripts/distill/glossary_update.py --root-id <R>` |
| 单票 Jira 附件/评论 REST 补拉 | `python3 scripts/jira/attachments/fetch_jira_attachments.py <KEY>` |
| 团队 SSOT | `python3 -c "from teams.registry import resolve_team"` |

## 包一览

```
runtime/   wiki/{sync,steps,lib}
jira/{run,steps,lib,d1,attachments}
distill/{coverage,proposition_extract,proposition_quality,domain_model_quality,s5_work_draft_quality,quality,domain_layout,s6_reader_quality,glossary_update,gate}
teams/{registry}
```
