"""Confluence extract orchestration (HTTP in extract_http)."""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import time
from argparse import Namespace
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from runtime.atlassian_env import ConfluenceEnv, load_dotenv
from wiki.lib.confluence_attachment_extract import (
    INVENTORY_DEFAULT_NAME,
    extract_page_attachments,
)
from wiki.lib.confluence_classify_utils import call_classify
from wiki.lib.confluence_kb_zh_display import ensure_zh_display, maybe_zh_title
from wiki.lib.extract_http import fetch_page, pick_page_body
from wiki.lib.extract_logic import (
    choose_extract_workers,
    parse_page_id_list,
)


def run_extract(args: Namespace, *, repo_root: Path) -> None:
    load_dotenv()
    conf = ConfluenceEnv.from_env(required=True)
    assert conf is not None
    auth = conf.auth_header()

    json_path: Path = args.json_path
    out_dir: Path = args.out_dir
    classify_mod: Path = args.classify_module
    product: str = args.product_name
    root_url: str = args.confluence_root_url

    classify = load_classify(classify_mod)
    index_path = out_dir / "README.md"

    rows = json.loads(json_path.read_text(encoding="utf-8"))
    if args.limit > 0:
        rows = rows[: args.limit]

    out_dir.mkdir(parents=True, exist_ok=True)

    attach_scope, attach_scope_err = build_attachment_scope(
        args.base_url,
        auth,
        args.attachment_pages,
        args.attachment_subroot,
        100,
    )
    if attach_scope_err:
        print(attach_scope_err, file=sys.stderr)
        raise SystemExit(2)
    if attach_scope is not None:
        print(
            f"confluence_extract_pages: selective attachments for "
            f"{len(attach_scope)} page id(s) (pages/subroot)",
            file=sys.stderr,
        )

    def want_attachments(page_id: str) -> bool:
        if attach_scope is not None:
            return page_id in attach_scope
        return bool(args.fetch_attachments)

    workers = resolve_extract_workers(args.workers, len(rows))
    iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    by_theme: Dict[str, list[str]] = {}
    errors: list[tuple[str, str]] = []
    rows_sorted: List[Dict[str, Any]] = sorted(rows, key=lambda r: int(r["id"]))

    def extract_one(row: Dict[str, Any]) -> Tuple[str, str, Optional[Tuple[str, str]]]:
        pid = str(row["id"])
        title = row.get("title") or ""
        web_ui = row.get("webUi") or ""
        display_title, title_confluence = maybe_zh_title(title)

        try:
            data, http_err = fetch_page(args.base_url, auth, pid)
            space_key = ""
            plain_raw = ""
            if http_err:
                plain = f"[提取失败]\n\n{http_err}"
                body_src = "error"
                note = ""
            elif data:
                plain_raw, body_src, note = pick_page_body(data)
                try:
                    space_key = (data.get("space") or {}).get("key") or ""
                except Exception:
                    pass
                if plain_raw.strip():
                    plain = ensure_zh_display(plain_raw)
                else:
                    plain = plain_raw
            else:
                plain, body_src, note = "", "empty", "未返回内容对象。"

            theme, kb = call_classify(classify, title, plain_raw or "")

            page_lines = [
                "---",
                f'title: {json.dumps(display_title, ensure_ascii=False)}',
            ]
            if title_confluence:
                page_lines.append(
                    f'title_confluence: {json.dumps(title_confluence, ensure_ascii=False)}'
                )
            page_lines.extend(
                [
                    f"page_id: {json.dumps(pid)}",
                    f'space_key: {json.dumps(space_key)}',
                    f'web_ui: {json.dumps(web_ui)}',
                    f'theme: {json.dumps(theme, ensure_ascii=False)}',
                    f'kb_outline: {json.dumps(kb, ensure_ascii=False)}',
                    f'extracted_at: {json.dumps(iso)}',
                    f'body_source: {json.dumps(body_src)}',
                    "---",
                    "",
                ]
            )
            if note:
                safe = note.replace("--", "— —")
                page_lines.append(f"<!-- {safe} -->")
                page_lines.append("")
            if plain:
                page_lines.append(plain)
            else:
                page_lines.append(
                    "_（此页无可用纯文本；若为白板、图表或宏，请在 Confluence 查看原页。）_"
                )

            view_html, storage_xml = "", ""
            if data and not http_err:
                body = data.get("body") or {}
                view_html = (body.get("view") or {}).get("value") or ""
                storage_xml = (body.get("storage") or {}).get("value") or ""

            inv_path = args.attachment_inventory or (out_dir.parent / INVENTORY_DEFAULT_NAME)
            if want_attachments(pid) and data and not http_err:
                md_att, att_errs = extract_page_attachments(
                    wiki_base=args.base_url,
                    auth_header=auth,
                    page_id=pid,
                    sleep_s=args.sleep,
                    max_bytes=args.attachment_max_bytes,
                    inventory_path=inv_path,
                    repo_root=repo_root,
                    body_view=view_html,
                    body_storage=storage_xml,
                )
                if md_att.strip():
                    page_lines.append(md_att.strip())
                for ae in att_errs:
                    print(ae, file=sys.stderr)

            out_file = out_dir / f"{pid}.md"
            out_file.write_text("\n".join(page_lines) + "\n", encoding="utf-8")

            idx_line = f"- [{display_title}]({pid}.md)"
            err_row = (pid, http_err) if http_err else None
            return theme, idx_line, err_row
        except Exception as exc:
            msg = f"{type(exc).__name__}: {exc}"
            stub = "\n".join(
                [
                    "---",
                    f'title: {json.dumps(f"[抽取异常] {pid}", ensure_ascii=False)}',
                    f"page_id: {json.dumps(pid)}",
                    'theme: "error"',
                    'kb_outline: "—"',
                    f'extracted_at: {json.dumps(iso)}',
                    'body_source: "error"',
                    "---",
                    "",
                    f"[抽取异常]\n\n{msg}",
                    "",
                ]
            )
            try:
                (out_dir / f"{pid}.md").write_text(stub + "\n", encoding="utf-8")
            except OSError:
                pass
            idx_line = f"- [{display_title}]({pid}.md)"
            return "error", idx_line, (pid, msg)

    if workers > 1:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(extract_one, row) for row in rows_sorted]
            for fut in as_completed(futures):
                theme, idx_line, err_row = fut.result()
                by_theme.setdefault(theme, []).append(idx_line)
                if err_row:
                    errors.append(err_row)
    else:
        for i, row in enumerate(rows_sorted):
            theme, idx_line, err_row = extract_one(row)
            by_theme.setdefault(theme, []).append(idx_line)
            if err_row:
                errors.append(err_row)
            if i + 1 < len(rows_sorted) and args.sleep > 0:
                time.sleep(args.sleep)

    worker_note = f" · **workers** {workers}" if workers > 1 else ""
    lines = [
        f"# {product} 子树 · 逐页正文提取（REST）",
        "",
        f"> **生成**：`scripts/wiki/steps/extract.py`（`--hui` 时为 Hui） · **UTC** {iso}{worker_note}",
        f"> **页数**：{len(rows)} · **输出**：每页一个 `<page_id>.md`（数字文件名即 Page ID）。",
        "",
        f"正文来自 **`body.view`（HTML 转纯文本）** 优先，否则 **`body.storage` 去标签**。白板、部分宏、图表可能仍为空，请以 [Confluence]({root_url}) 为准。",
        "",
        "若抽取时使用 **`--fetch-attachments`**（全量）、**`--attachment-pages`**（指定页）或 **`--attachment-subroot`**（子树），会在对应页文末追加「附件抽取」；盘点见同级 **`attachment-type-inventory.json`**。",
        "",
        "## 按主题分组（与领域归类一致）",
        "",
    ]
    for theme in sorted(by_theme.keys()):
        lines.append(f"### {theme}")
        lines.append("")
        lines.extend(by_theme[theme])
        lines.append("")

    if errors:
        lines.append("## 提取失败")
        lines.append("")
        for pid, msg in errors:
            lines.append(f"- `{pid}`: {msg[:200]}")
        lines.append("")

    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {len(rows)} files under {out_dir}", file=sys.stderr)
    print(f"Index: {index_path}", file=sys.stderr)
    if errors:
        print(f"Errors: {len(errors)}", file=sys.stderr)

    report_path = args.write_report
    report_payload = {
        "json_source": str(json_path.resolve()),
        "out_dir": str(out_dir.resolve()),
        "enumerated_page_count": len(rows),
        "page_ids": [str(r["id"]) for r in rows_sorted],
        "error_count": len(errors),
        "errors": [{"page_id": pid, "message": msg} for pid, msg in errors],
    }
    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(report_payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"Report: {report_path}", file=sys.stderr)

    print("", file=sys.stderr)
    print("--- confluence_extract_pages: summary ---", file=sys.stderr)
    print(
        f"Planned pages (rows in JSON): {len(rows)} · Output dir: {out_dir}",
        file=sys.stderr,
    )
    print(
        f"Completed writes: {len(rows)} files · API/extract failures: {len(errors)}",
        file=sys.stderr,
    )
    if errors:
        cap = 25
        for pid, msg in errors[:cap]:
            tail = (msg or "").replace("\n", " ").strip()
            if len(tail) > 280:
                tail = tail[:277] + "..."
            print(f"  FAIL page_id={pid}: {tail}", file=sys.stderr)
        if len(errors) > cap:
            print(
                f"  ... {len(errors) - cap} more (see pages/README.md ## 提取失败 "
                f"or --write-report JSON)",
                file=sys.stderr,
            )
    print("--- end extract summary ---", file=sys.stderr)


def load_classify(script_path: Path):
    spec = importlib.util.spec_from_file_location("cov_dyn", script_path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod.classify


def build_attachment_scope(
    base_url: str,
    auth: str,
    attachment_pages: str,
    attachment_subroot: str,
    page_size: int,
) -> Tuple[Optional[Set[str]], Optional[str]]:
    scope: Optional[Set[str]] = None
    pages = parse_page_id_list(attachment_pages)
    sub = (attachment_subroot or "").strip()
    if sub:
        if not sub.isdigit():
            return None, f"invalid --attachment-subroot (expect digits): {attachment_subroot!r}"
        from wiki.lib.enumerate_http import enumerate_descendants

        scope = {sub}
        try:
            for page in enumerate_descendants(
                base_url, auth, sub, max(1, min(page_size, 250))
            ):
                cid = str(page.get("id") or "").strip()
                if cid:
                    scope.add(cid)
        except SystemExit as exc:
            return None, str(exc)
    if pages:
        scope = (scope or set()) | pages
    return scope, None


def resolve_extract_workers(cli: Optional[int], page_count: int) -> int:
    workers, reason = choose_extract_workers(page_count, cli=cli)
    mode = "parallel" if workers > 1 else "sequential"
    print(
        f"confluence_extract_pages: workers={workers} ({mode}, {reason})",
        file=sys.stderr,
    )
    return workers
