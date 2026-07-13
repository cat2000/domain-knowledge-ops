"""Scripts 运行时：路径常量与 ``sys.path`` 引导（供 ``*/steps`` 子进程使用）。"""

from runtime.bootstrap import ensure_scripts_on_path
from runtime.paths import REPO_ROOT, SCRIPTS_DIR

__all__ = ["REPO_ROOT", "SCRIPTS_DIR", "ensure_scripts_on_path"]
