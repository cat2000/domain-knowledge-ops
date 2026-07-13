"""
S1 Confluence sync — idempotent step runner.

Each step overwrites its outputs from upstream artifacts (safe to re-run):

  1. enumerate  → ``_subtree_enumeration.json``
  2. merge      → ``descendants-full.json`` (merge-by page id)
  3. extract    → ``pages/*.md`` + ``_last_extract_report.json``
  4. coverage   → ``source-coverage.md``
  5. materialize → ``materialized/by-root/<id>/``
  6. handoff    → ``PIPELINE_HANDOFF.json``
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from wiki.sync import pipeline_logic as pl
from wiki.sync.canonical import (
    canonical_root_ids_from_env,
    env_resolve_canonical_flag,
    resolve_canonical_sync_root,
)
from wiki.sync.env import FACET_CLASSIFY_MODULE, preferred_python
from runtime.paths import REPO_ROOT
from wiki.sync.handoff import write_pipeline_handoff
from wiki.sync.helpers import coerce_enum_page_size, orchestrator_extract_workers, run_cmd
from wiki.sync.labels import KNOWN_ROOT_LABELS, default_root_label_url
from wiki.sync.pipeline_types import SyncConfig, SyncPaths, SyncRoots
from wiki.sync.root_resolve import (
    basic_auth_header,
    fetch_ancestor_ids,
    fetch_space_homepage_page_id,
    fetch_space_key_for_page,
    parse_page_id,
    space_key_from_space_overview_url,
    try_parse_page_id,
)
from wiki.sync.storage_root import resolve_storage_root_for_subtree

LOG_PREFIX = "sync_domain_knowledge_from_confluence"
SCRIPTS = REPO_ROOT / "scripts"
STEP_SCRIPTS = {
    "enumerate": SCRIPTS / "wiki/steps/enumerate.py",
    "extract": SCRIPTS / "wiki/steps/extract.py",
    "coverage": SCRIPTS / "wiki/steps/source_coverage.py",
    "materialize": SCRIPTS / "wiki/steps/materialize.py",
}


def run_s1_sync(config: SyncConfig) -> None:
    """Execute idempotent S1 pipeline: enumerate → merge → extract → coverage → materialize."""
    wiki_base = _wiki_base()
    pasted_id, used_space_overview = resolve_pasted_page_id(config.raw_input, wiki_base)
    roots = resolve_sync_roots(config, pasted_id, used_space_overview, wiki_base)
    paths = SyncPaths.for_storage_root(REPO_ROOT, roots.storage_root_id)
    paths.ensure_extracted_base()

    page_count = step_enumerate(config, roots, paths)
    step_merge_inventory(roots, paths)
    step_extract(config, roots, paths, page_count=page_count)
    extract_report = print_extract_summary(roots, paths, page_count)
    s1_status = pl.s1_status_from_extract_report(extract_report)
    if s1_status == "partial" and not config.allow_partial:
        error_count = pl.extract_error_count(extract_report)
        raise SystemExit(
            f"{LOG_PREFIX}: S1 extract is partial ({error_count} page error(s)); "
            "fix extraction or rerun with --allow-partial to write a partial handoff explicitly."
        )
    step_coverage(roots, paths)

    if not config.skip_materialize:
        step_materialize(roots, paths)
    step_handoff(config, roots, paths, s1_status=s1_status, extract_report=extract_report)
    print_done(config, roots, paths, page_count)


def resolve_pasted_page_id(raw: str, wiki_base: str) -> Tuple[str, bool]:
    """Return (pasted page id, used_space_overview)."""
    pasted_opt = try_parse_page_id(raw)
    space_key = space_key_from_space_overview_url(raw)
    if pasted_opt:
        return pasted_opt, False
    if space_key:
        email, token = _atlassian_auth()
        if not email or not token:
            raise SystemExit(
                "Could not parse page ID from --url/--root. "
                "For …/spaces/<KEY>/overview (no /pages/<id>/ or homepageId=), set "
                "ATLASSIAN_EMAIL and ATLASSIAN_API_TOKEN so the Space homepage can be resolved via REST."
            )
        try:
            resolved = fetch_space_homepage_page_id(
                wiki_base, basic_auth_header(email, token), space_key
            )
        except RuntimeError as exc:
            raise SystemExit(
                f"Could not resolve Space {space_key!r} homepage: {exc}"
            ) from exc
        if not resolved:
            raise SystemExit(
                f"Space {space_key!r} returned no homepage id "
                "(check the space exists and your account can read it)."
            )
        _log(f"Space overview {space_key!r} → homepage page id {resolved}")
        return resolved, True
    return parse_page_id(raw), False


def resolve_sync_roots(
    config: SyncConfig,
    pasted_id: str,
    used_space_overview: bool,
    wiki_base: str,
) -> SyncRoots:
    canonical_ids = canonical_root_ids_from_env()
    lift_enabled, warn_empty = pl.should_enable_canonical_lift(
        config.resolve_canonical_root,
        env_resolve_canonical_flag(),
        canonical_ids,
    )
    if warn_empty:
        _log(
            "ancestor promotion requested but CONFLUENCE_CANONICAL_ROOT_IDS "
            "is empty — using pasted page as enumeration root."
        )

    ancestor_ids: List[str] = []
    if lift_enabled:
        email, token = _atlassian_auth()
        if email and token:
            try:
                ancestor_ids = fetch_ancestor_ids(
                    wiki_base, basic_auth_header(email, token), pasted_id
                )
            except Exception as exc:
                _log(
                    f"could not fetch ancestors for page {pasted_id}: {exc}; "
                    "using pasted page as sync root (ancestor promotion skipped)."
                )
        else:
            _log(
                "ATLASSIAN_EMAIL / ATLASSIAN_API_TOKEN missing; "
                "cannot evaluate ancestor promotion — using pasted page as sync root."
            )

    enum_root_id, lifted = resolve_canonical_sync_root(
        pasted_id,
        ancestor_ids,
        enabled=lift_enabled,
        canonical_root_ids=canonical_ids,
    )
    if lifted:
        label = (
            KNOWN_ROOT_LABELS[enum_root_id][0]
            if enum_root_id in KNOWN_ROOT_LABELS
            else f"Root {enum_root_id}"
        )
        _log(
            f"pasted page {pasted_id} → promoted enumeration root {enum_root_id} ({label})."
        )

    reuse_ok = pl.resolve_reuse_enabled(
        config.no_reuse_existing_by_root,
        pl.env_reuse_existing_by_root(
            os.environ.get("CONFLUENCE_REUSE_EXISTING_BY_ROOT", "")
        ),
        used_space_overview,
    )
    storage_root_id, _ = resolve_storage_root_for_subtree(
        enum_root_id, wiki_base, reuse_ok
    )

    if lifted:
        root_label, root_url = default_root_label_url(enum_root_id, None)
    else:
        root_label, root_url = default_root_label_url(enum_root_id, config.url_arg)

    return SyncRoots(
        pasted_id=pasted_id,
        enum_root_id=enum_root_id,
        storage_root_id=storage_root_id,
        root_label=root_label,
        root_url=root_url,
        used_space_overview=used_space_overview,
        lifted=lifted,
    )


def step_enumerate(config: SyncConfig, roots: SyncRoots, paths: SyncPaths) -> int:
    """Write ``_subtree_enumeration.json``; return row count for this subtree."""
    enum_page_size = coerce_enum_page_size(config.enum_page_size)
    cql_query: Optional[str] = None
    if config.enum_mode == "cql":
        cql_query = _resolve_cql_query(config, roots, _wiki_base())

    cmd = pl.build_enumerate_command(
        python=preferred_python(),
        script=STEP_SCRIPTS["enumerate"],
        enum_page_size=enum_page_size,
        subtree_json=paths.subtree_enum,
        enum_mode=config.enum_mode,
        enum_root_id=roots.enum_root_id,
        cql_query=cql_query,
    )
    _log(f"enum page-size={enum_page_size} (CQL limit / BFS batch)")
    run_cmd(cmd)
    return len(pl.read_json_rows(paths.subtree_enum))


def _resolve_cql_query(config: SyncConfig, roots: SyncRoots, wiki_base: str) -> str:
    explicit = (config.cql or os.environ.get("CONFLUENCE_ENUMERATE_CQL", "")).strip()
    if explicit:
        _log(f"enum-mode cql (explicit query, {len(explicit)} chars)")
        return explicit

    email, token = _atlassian_auth()
    if not email or not token:
        raise SystemExit(
            f"{LOG_PREFIX}: CQL enumeration without explicit --cql requires "
            "ATLASSIAN_EMAIL + ATLASSIAN_API_TOKEN (to resolve space key) or set "
            "CONFLUENCE_ENUMERATE_CQL / pass --cql."
        )
    space_key = fetch_space_key_for_page(
        wiki_base, basic_auth_header(email, token), roots.enum_root_id
    )
    if not space_key:
        raise SystemExit(
            f"{LOG_PREFIX}: could not resolve space key for auto CQL; pass --cql explicitly."
        )
    cql = pl.build_auto_subtree_cql(space_key, roots.enum_root_id)
    _log(f"enum-mode cql (auto subtree): {cql}")
    return cql


def step_merge_inventory(roots: SyncRoots, paths: SyncPaths) -> None:
    """Merge subtree enumeration into ``descendants-full.json`` (idempotent by page id)."""
    subtree_rows = pl.read_json_rows(paths.subtree_enum)
    existing_rows = pl.read_json_rows(paths.descendants_full)
    inventory_rows, merged = pl.merge_descendants_inventory(
        existing_rows,
        subtree_rows,
        roots.storage_root_id,
        roots.enum_root_id,
    )
    pl.write_json_artifact(paths.descendants_full, inventory_rows)
    if merged:
        _log(
            f"merged {len(subtree_rows)} enumerated row(s) into "
            f"{paths.descendants_full.relative_to(REPO_ROOT)} (total {len(inventory_rows)} pages)"
        )


def step_extract(
    config: SyncConfig,
    roots: SyncRoots,
    paths: SyncPaths,
    *,
    page_count: int,
) -> None:
    """Refresh ``pages/*.md`` from current subtree enumeration."""
    workers, workers_src = orchestrator_extract_workers(
        config.extract_workers, page_count
    )
    _log(f"extract workers={workers} ({workers_src})")

    attach_pages = (
        config.attachment_pages or os.environ.get("CONFLUENCE_ATTACHMENT_PAGES", "")
    ).strip()
    attach_subroot = (
        config.attachment_subroot or os.environ.get("CONFLUENCE_ATTACHMENT_SUBROOT", "")
    ).strip()
    attach_mode = pl.resolve_attachments_mode(
        config.attachments_mode,
        os.environ.get("CONFLUENCE_ATTACHMENTS", ""),
    )
    attach_pages, attach_subroot = pl.apply_attachments_mode(
        attach_mode, roots.pasted_id, attach_pages, attach_subroot
    )
    if attach_mode == "page":
        _log(
            f"--attachments page → attachment-pages includes pasted page {roots.pasted_id}"
        )
    elif attach_mode == "tree":
        _log(
            f"--attachments tree → --attachment-subroot {roots.pasted_id} "
            "(pasted page and descendants)"
        )

    fetch_attachments = pl.resolve_fetch_attachments(
        config.fetch_attachments,
        os.environ.get("CONFLUENCE_FETCH_ATTACHMENTS", ""),
    )
    cmd = pl.build_extract_command(
        python=preferred_python(),
        script=STEP_SCRIPTS["extract"],
        subtree_json=paths.subtree_enum,
        pages_dir=paths.pages_dir,
        classify_module=FACET_CLASSIFY_MODULE,
        product_tag=pl.product_tag_for_sync(roots.enum_root_id, roots.storage_root_id),
        root_url=roots.root_url,
        workers=workers,
        fetch_attachments=fetch_attachments,
        attachment_pages=attach_pages,
        attachment_subroot=attach_subroot,
        extract_report=paths.extract_report,
    )
    run_cmd(cmd)


def print_extract_summary(roots: SyncRoots, paths: SyncPaths, page_count: int) -> dict:
    print("", file=sys.stderr)
    print(f"======== {LOG_PREFIX} · run summary ========", file=sys.stderr)
    print(
        f"Enumeration root: {roots.enum_root_id} · Storage root: {roots.storage_root_id}",
        file=sys.stderr,
    )
    print(
        f"This run · CQL/BFS enumerated: {page_count} page(s) "
        f"(rows in _subtree_enumeration.json)",
        file=sys.stderr,
    )
    try:
        inv_after = len(pl.read_json_rows(paths.descendants_full))
        print(
            f"descendants-full.json · row count after this run: {inv_after}",
            file=sys.stderr,
        )
        if roots.storage_root_id != roots.enum_root_id:
            print(
                "  Note: merged inventory — total rows increase when new page IDs appear "
                "in Confluence or prior rows were missing; not equivalent to “only this subtree”.",
                file=sys.stderr,
            )
    except OSError:
        pass

    if not paths.extract_report.is_file():
        _log("no extract report file (unexpected)")
        print("=========================================================", file=sys.stderr)
        print("", file=sys.stderr)
        return {}

    try:
        report = pl.read_extract_report(paths.extract_report)
        planned = int(report.get("enumerated_page_count", page_count))
        error_count = int(report.get("error_count", 0))
        print(
            f"Extract step · planned rows: {planned} · "
            f"REST/extract errors logged: {error_count} "
            f"(each row still gets a .md stub unless worker crashed)",
            file=sys.stderr,
        )
        if error_count:
            print(
                "  Failure reasons (first pages); stubs may still exist on disk:",
                file=sys.stderr,
            )
            for entry in (report.get("errors") or [])[:20]:
                page_id = entry.get("page_id", "")
                message = (entry.get("message") or "").replace("\n", " ").strip()
                if len(message) > 240:
                    message = message[:237] + "..."
                print(f"    · {page_id}: {message}", file=sys.stderr)
            if error_count > 20:
                print(f"    · … plus {error_count - 20} more", file=sys.stderr)
        print(
            f"Detail JSON: {paths.extract_report.relative_to(REPO_ROOT)}",
            file=sys.stderr,
        )
    except (json.JSONDecodeError, OSError, TypeError, ValueError) as exc:
        _log(f"could not read extract report: {exc}")
        report = {}

    print("=========================================================", file=sys.stderr)
    print("", file=sys.stderr)
    return report


def step_coverage(roots: SyncRoots, paths: SyncPaths) -> None:
    """Regenerate ``source-coverage.md`` from inventory + pages."""
    cmd = pl.build_coverage_command(
        python=preferred_python(),
        script=STEP_SCRIPTS["coverage"],
        descendants_full=paths.descendants_full,
        coverage_md=paths.coverage_md,
        classify_module=FACET_CLASSIFY_MODULE,
        storage_root_id=roots.storage_root_id,
        root_url=roots.root_url,
        root_label=roots.root_label,
        pages_dir=paths.pages_dir,
    )
    run_cmd(cmd)


def step_materialize(roots: SyncRoots, paths: SyncPaths) -> None:
    """Regenerate ``materialized/by-root/<id>/`` from extracted pages."""
    cmd = pl.build_materialize_command(
        python=preferred_python(),
        script=STEP_SCRIPTS["materialize"],
        pages_dir=paths.pages_dir,
        rules_base=paths.rules_base,
        storage_root_id=roots.storage_root_id,
    )
    run_cmd(cmd)


def step_handoff(
    config: SyncConfig,
    roots: SyncRoots,
    paths: SyncPaths,
    *,
    s1_status: str,
    extract_report: dict,
) -> None:
    if config.skip_materialize or config.no_distill_handoff:
        if not config.skip_materialize and config.no_distill_handoff:
            _log("skipped PIPELINE_HANDOFF (--no-distill-handoff)")
        return
    handoff_path = write_pipeline_handoff(
        roots.storage_root_id,
        paths.extracted_base,
        paths.rules_base,
        enumeration_root_page_id=(
            roots.enum_root_id if roots.storage_root_id != roots.enum_root_id else None
        ),
        s1_status=s1_status,
        extract_error_count=pl.extract_error_count(extract_report),
    )
    _log(
        f"PIPELINE_HANDOFF → {handoff_path.relative_to(REPO_ROOT)} "
        f"(Cursor: RUNBOOK S2–S3 tag+aggregate, S4–S5 distill+zh — see PIPELINE_HANDOFF)"
    )


def print_done(config: SyncConfig, roots: SyncRoots, paths: SyncPaths, page_count: int) -> None:
    if not config.skip_materialize:
        enum_hint = (
            f", enumeration root `{roots.enum_root_id}`"
            if roots.storage_root_id != roots.enum_root_id
            else ""
        )
        _log(
            "SAME-CHAT → `@generate-knowledge-from-wiki` RUNBOOK S2 "
            f"(root `{roots.storage_root_id}`{enum_hint}); 继续 runs S3–S6 after 确认 on checklist."
        )

    enum_done = (
        f" enumeration_root={roots.enum_root_id}"
        if roots.storage_root_id != roots.enum_root_id
        else ""
    )
    rules_note = (
        "" if config.skip_materialize else f"; rules → {paths.rules_base.relative_to(REPO_ROOT)}"
    )
    _log(
        f"Done [storage_root {roots.storage_root_id}{enum_done}]: {page_count} page(s) in this run → "
        f"{paths.extracted_base.relative_to(REPO_ROOT)}; coverage + pages updated{rules_note}"
    )
    if not config.skip_materialize:
        _log(
            "curated/ NOT written here — "
            "Cursor RUNBOOK S2–S4 (no translation); zh-CN only in S5 _deliver/定稿.md."
        )


def _log(message: str) -> None:
    print(f"{LOG_PREFIX}: {message}", file=sys.stderr)


def _wiki_base() -> str:
    from runtime.atlassian_env import DEFAULT_CONFLUENCE_BASE

    return os.environ.get("CONFLUENCE_BASE_URL", DEFAULT_CONFLUENCE_BASE).strip()


def _atlassian_auth() -> Tuple[str, str]:
    return (
        os.environ.get("ATLASSIAN_EMAIL", "").strip(),
        os.environ.get("ATLASSIAN_API_TOKEN", "").strip(),
    )
