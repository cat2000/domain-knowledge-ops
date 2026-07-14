# generate-knowledge-from-wiki · S1 同步 CLI（参数 / 排障）

> English SSOT: [`S1-SYNC-CLI.md`](./S1-SYNC-CLI.md).
>
> **执行剧本**：[`RUNBOOK.md`](./RUNBOOK.md) · **用户入口**：[`SKILL.md`](./SKILL.md)

## 链接解析

粘贴 **Confluence 链接或数字 ID** → **粘贴页 ID**（支持 `/pages/<id>/`、`homepageId=`、`…/spaces/<KEY>/overview` 经 REST 取 homepage、正文内长数字 ID）。

- **默认**：粘贴页 = **枚举根**，拉整棵后代 → `extracted/by-root/<ID>/`、`materialized/by-root/<ID>/`（落盘根可能因复用而与枚举根不同，见 domain-knowledge-pipeline-contract §2）。
- **团队整库**：粘贴 **本 Space overview / homepage**，勿把产品分组 / 渠道子树页当默认权威根。
- **祖先升格**（可选）：`.env` 中 `CONFLUENCE_CANONICAL_ROOT_IDS` + `--resolve-canonical-root` 或 `CONFLUENCE_RESOLVE_CANONICAL_ROOT=1`。

## 编排脚本内部顺序

入口：`scripts/sync_domain_knowledge_from_confluence.py`（优先 `.venv/bin/python3`）。

1. `confluence_enumerate_child_pages.py` → `descendants-full.json`  
   - 默认 **`enum-mode=cql`**（分页，`--page-size` / `CONFLUENCE_ENUMERATE_PAGE_SIZE`，1–250）  
   - 可选 **`--enum-mode bfs`** / `CONFLUENCE_ENUM_MODE=bfs`
2. `confluence_extract_pages.py` → `pages/<PAGE_ID>.md`（`kb_outline`）  
   - `--workers` / `CONFLUENCE_EXTRACT_WORKERS`  
   - 默认 **不拉附件**；`--attachments page|tree` 或进阶 `CONFLUENCE_FETCH_ATTACHMENTS` 等
3. 完整性门禁：`_last_extract_report.json` 有 `error_count > 0` 时默认停止；显式 `--allow-partial` 才继续，并写 partial handoff
4. `gen_source_coverage.py`
5. `materialize_rules_from_extracted.py`（`--skip-materialize` 可跳过）  
   - 写 `_materialized_manifest.json`
   - 清理当前 source set 不再生成的旧 materialized `.md`

**`curated/`**：脚本 **不写**；由 Agent 按 [`RUNBOOK.md`](./RUNBOOK.md)（S2–S3 `_aggregate/`、S4–S5 `_deliver/`）写入。

## 耗时与翻译

- 耗时 ≈ 子树页数 × HTTP + 默认 sleep；附件/OCR 显著更慢。
- **勿**默认 `CONFLUENCE_KB_TRANSLATE=1`（抽取阶段在线翻译，大子树极慢）。简体中文 **仅** 在 **S5** `_deliver/…定稿.md`。

## 命令速查

```bash
python3 scripts/sync_domain_knowledge_from_confluence.py --url "<PAGE_URL_OR_ID>"
python3 scripts/sync_domain_knowledge_from_confluence.py --root "<PAGE_ID>"
python3 scripts/sync_domain_knowledge_from_confluence.py --url "..." --attachments tree
python3 scripts/sync_domain_knowledge_from_confluence.py --url "..." --no-reuse-existing-by-root
python3 scripts/sync_domain_knowledge_from_confluence.py --url "..." --enum-mode bfs
python3 scripts/sync_domain_knowledge_from_confluence.py --url "..." --allow-partial
```

## 故障排查

| 现象 | 处理 |
|------|------|
| `HTTP 401/403` | 邮箱、API token、空间权限 |
| `Set ATLASSIAN_EMAIL` | 配置 `.env` |
| 很慢 | 子树页数 × HTTP；预期 |
| `S1 extract is partial` | 修复抽取错误后重跑；只有确认缺页不影响后续时才加 `--allow-partial` |

## `kb_outline` 为 `—`

该页不进规则聚合；仍可在 `extracted/.../pages/<PAGE_ID>.md` 查看抽取正文。
