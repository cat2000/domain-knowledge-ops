"""Pure helpers for wiki S1 sync pipeline (testable without HTTP)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from wiki.lib.extract_logic import choose_extract_workers
from wiki.sync.storage_root import merge_descendants_rows


def write_json_artifact(path: Path, data: object) -> None:
    """Overwrite JSON artifact (idempotent write — same input → same file)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def read_json_rows(path: Path) -> List[Dict[str, Any]]:
    if not path.is_file():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        return []
    return [row for row in raw if isinstance(row, dict)]


def extract_error_count(report: Dict[str, Any]) -> int:
    """Return the deterministic extraction error count from an extract report."""
    try:
        return int(report.get("error_count") or 0)
    except (TypeError, ValueError):
        return 0


def read_extract_report(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    return raw if isinstance(raw, dict) else {}


def s1_status_from_extract_report(report: Dict[str, Any]) -> str:
    return "partial" if extract_error_count(report) > 0 else "complete"


def build_enumerate_command(
    *,
    python: str,
    script: Path,
    enum_page_size: int,
    subtree_json: Path,
    enum_mode: str,
    enum_root_id: str,
    cql_query: Optional[str],
) -> List[str]:
    cmd = [
        python,
        str(script),
        "--page-size",
        str(enum_page_size),
        "--json",
        str(subtree_json),
    ]
    if enum_mode == "cql" and cql_query:
        cmd.extend(["--cql", cql_query])
    else:
        cmd.extend(["--root", enum_root_id])
    return cmd


def build_extract_command(
    *,
    python: str,
    script: Path,
    subtree_json: Path,
    pages_dir: Path,
    classify_module: Path,
    product_tag: str,
    root_url: str,
    workers: int,
    fetch_attachments: bool,
    attachment_pages: str,
    attachment_subroot: str,
    extract_report: Path,
) -> List[str]:
    cmd = [
        python,
        str(script),
        "--json-path",
        str(subtree_json),
        "--out-dir",
        str(pages_dir),
        "--classify-module",
        str(classify_module),
        "--product-name",
        product_tag,
        "--confluence-root-url",
        root_url,
        "--workers",
        str(workers),
    ]
    if fetch_attachments:
        cmd.append("--fetch-attachments")
    if attachment_pages:
        cmd.extend(["--attachment-pages", attachment_pages])
    if attachment_subroot:
        cmd.extend(["--attachment-subroot", attachment_subroot])
    cmd.extend(["--write-report", str(extract_report)])
    return cmd


def build_coverage_command(
    *,
    python: str,
    script: Path,
    descendants_full: Path,
    coverage_md: Path,
    classify_module: Path,
    storage_root_id: str,
    root_url: str,
    root_label: str,
    pages_dir: Path,
) -> List[str]:
    return [
        python,
        str(script),
        "--json",
        str(descendants_full),
        "--out",
        str(coverage_md),
        "--classify-module",
        str(classify_module),
        "--root-page-id",
        storage_root_id,
        "--root-url",
        root_url,
        "--root-label",
        root_label,
        "--pages-dir",
        str(pages_dir),
    ]


def build_materialize_command(
    *,
    python: str,
    script: Path,
    pages_dir: Path,
    rules_base: Path,
    storage_root_id: str,
) -> List[str]:
    return [
        python,
        str(script),
        "--extracted-dir",
        str(pages_dir),
        "--rules-base",
        str(rules_base),
        "--root-page-id",
        storage_root_id,
    ]


def default_enum_mode(env_value: str = "") -> str:
    value = (env_value or "").strip().lower()
    return value if value in ("bfs", "cql") else "cql"


def coerce_enum_page_size(cli_value: Optional[int], env_value: str = "") -> int:
    if cli_value is not None:
        return max(1, min(int(cli_value), 250))
    env = (env_value or "").strip()
    if env.isdigit():
        return max(1, min(int(env), 250))
    return 250


def merge_page_ids(existing_csv: str, *extras: str) -> str:
    seen: set[str] = set()
    out: List[str] = []
    for part in (existing_csv or "").split(","):
        token = part.strip()
        if token.isdigit() and token not in seen:
            seen.add(token)
            out.append(token)
    for extra in extras:
        value = (extra or "").strip()
        if value.isdigit() and value not in seen:
            seen.add(value)
            out.append(value)
    return ",".join(out)


def orchestrator_extract_workers(
    cli_workers: Optional[int],
    page_count: int,
    env_workers: str = "",
    *,
    cpu_count: Optional[int] = None,
) -> Tuple[int, str]:
    env = (env_workers or "").strip()
    env_int = int(env) if env.isdigit() else None
    workers, reason = choose_extract_workers(
        page_count,
        cli=cli_workers,
        env_workers=env_int,
        cpu_count=cpu_count,
    )
    if reason == "--workers":
        return workers, "--extract-workers"
    if reason == "CONFLUENCE_EXTRACT_WORKERS":
        return workers, "CONFLUENCE_EXTRACT_WORKERS"
    return workers, f"auto from {page_count} enumerated pages"


def env_reuse_existing_by_root(env_value: str = "") -> bool:
    value = (env_value or "").strip().lower()
    if value in ("0", "false", "no", "off"):
        return False
    return True


def build_auto_subtree_cql(space_key: str, enum_root_id: str) -> str:
    return (
        f'space = "{space_key}" AND type = page AND '
        f"(id = {enum_root_id} OR ancestor = {enum_root_id}) ORDER BY title"
    )


def resolve_attachments_mode(cli_mode: Optional[str], env_value: str) -> str:
    if cli_mode in ("off", "page", "tree"):
        return cli_mode
    env_mode = (env_value or "").strip().lower()
    return env_mode if env_mode in ("off", "page", "tree") else "off"


def apply_attachments_mode(
    attach_mode: str,
    pasted_id: str,
    attach_pages: str,
    attach_subroot: str,
) -> Tuple[str, str]:
    pages = attach_pages
    subroot = attach_subroot
    if attach_mode == "page":
        pages = merge_page_ids(pages, pasted_id)
    elif attach_mode == "tree":
        subroot = pasted_id
    return pages, subroot


def resolve_fetch_attachments(cli_flag: bool, env_value: str) -> bool:
    enabled = bool(cli_flag)
    env = (env_value or "").strip().lower()
    if env in ("1", "true", "yes"):
        enabled = True
    elif env in ("0", "false", "no", "off"):
        enabled = False
    return enabled


def product_tag_for_sync(enum_root_id: str, storage_root_id: str) -> str:
    if storage_root_id != enum_root_id:
        return (
            f"Confluence subtree · enum {enum_root_id} · storage {storage_root_id}"
        )
    return f"Confluence subtree · root {enum_root_id}"


def merge_descendants_inventory(
    existing_rows: List[Dict[str, Any]],
    subtree_rows: List[Dict[str, Any]],
    storage_root_id: str,
    enum_root_id: str,
) -> Tuple[List[Dict[str, Any]], bool]:
    if storage_root_id != enum_root_id:
        return merge_descendants_rows(existing_rows, subtree_rows), True
    return subtree_rows, False


def resolve_reuse_enabled(
    cli_no_reuse: bool,
    env_reuse: bool,
    used_space_overview: bool,
) -> bool:
    if cli_no_reuse or used_space_overview:
        return False
    return env_reuse


def should_enable_canonical_lift(
    cli_flag: bool,
    env_flag: bool,
    canonical_ids: Tuple[str, ...],
) -> Tuple[bool, bool]:
    want_lift = bool(cli_flag or env_flag)
    if want_lift and not canonical_ids:
        return False, True
    return want_lift and bool(canonical_ids), False
