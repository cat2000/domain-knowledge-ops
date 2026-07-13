# Tests

重构后的回归网（无需 Confluence/Jira 凭证）。

```bash
# 从仓库根目录
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

覆盖：目录布局、**domain-knowledge 文档契约**、**无 deprecated 脚本产物**、**distill / wiki / jira 纯逻辑单测**（`*_logic.py`、`pipeline_logic.py`）、Wiki S1 CLI、团队 SSOT、`domain_check` 门面、CLI `-h`、`compileall`、**确认闸门**、**S1–S6 命名**。共享辅助：`contract_support.py`。
