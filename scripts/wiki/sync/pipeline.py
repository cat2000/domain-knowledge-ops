"""Stage-1 Confluence sync orchestration (enumerate → extract → coverage → rules)."""

from __future__ import annotations

import argparse
import os

from wiki.sync.env import load_dotenv
from wiki.sync.helpers import default_enum_mode
from wiki.sync import pipeline_logic as pl
from wiki.sync.pipeline_run import run_s1_sync
from wiki.sync.pipeline_types import SyncConfig


def main() -> None:
    load_dotenv()
    parser = build_parser()
    args = parser.parse_args()
    if not (args.root or args.url):
        parser.error("Provide --root or --url")
    run_s1_sync(config_from_args(args))


def config_from_args(args: argparse.Namespace) -> SyncConfig:
    raw = args.root or args.url
    if not raw:
        raise ValueError("Provide --root or --url")
    return SyncConfig(
        raw_input=raw,
        url_arg=args.url,
        skip_materialize=bool(args.skip_materialize),
        no_distill_handoff=bool(args.no_distill_handoff),
        fetch_attachments=pl.resolve_fetch_attachments(
            bool(args.fetch_attachments),
            os.environ.get("CONFLUENCE_FETCH_ATTACHMENTS", ""),
        ),
        attachment_pages=(args.attachment_pages or "").strip(),
        attachment_subroot=(args.attachment_subroot or "").strip(),
        attachments_mode=args.attachments,
        allow_partial=bool(args.allow_partial),
        resolve_canonical_root=bool(args.resolve_canonical_root),
        no_reuse_existing_by_root=bool(args.no_reuse_existing_by_root),
        enum_mode=args.enum_mode,
        cql=(args.cql or "").strip(),
        enum_page_size=args.enum_page_size,
        extract_workers=args.extract_workers,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Sync KB inventory + extract from any Confluence root page."
    )
    parser.add_argument("--root", help="Root page ID (decimal string)")
    parser.add_argument("--url", help="Confluence page URL (alternative to --root)")
    parser.add_argument(
        "--skip-materialize",
        action="store_true",
        help="Skip writing domain-knowledge/materialized/by-root/<id>/ from kb_outline",
    )
    parser.add_argument(
        "--no-distill-handoff",
        action="store_true",
        help="Do not write domain-knowledge/extracted/by-root/<id>/PIPELINE_HANDOFF.json (Cursor stage-2 cue).",
    )
    parser.add_argument(
        "--fetch-attachments",
        action="store_true",
        help=(
            "Pass --fetch-attachments to the extract step (download attachments + body-linked files + OCR). "
            "Default is off for speed. Or set CONFLUENCE_FETCH_ATTACHMENTS=1."
        ),
    )
    parser.add_argument(
        "--attachment-pages",
        default="",
        help=(
            "Comma-separated page IDs: attachments only for these pages (passed to extract step). "
            "Env: CONFLUENCE_ATTACHMENT_PAGES."
        ),
    )
    parser.add_argument(
        "--attachment-subroot",
        default="",
        help=(
            "Page ID: attachments for this page and all descendants (BFS). Env: CONFLUENCE_ATTACHMENT_SUBROOT."
        ),
    )
    parser.add_argument(
        "--attachments",
        choices=("off", "page", "tree"),
        default=None,
        metavar="MODE",
        help=(
            "One-shot attachment scope from the pasted --url/--root page ID: "
            "off = none (default); page = that page only; tree = that page plus all descendants. "
            "Ignored pieces: enumeration root / canonical lift — attachments follow the pasted link. "
            "Env: CONFLUENCE_ATTACHMENTS (same values)."
        ),
    )
    parser.add_argument(
        "--allow-partial",
        action="store_true",
        help=(
            "Allow S1 to continue when extraction reports page errors. "
            "Default: fail before coverage/materialize/handoff so incomplete source sync cannot enter S2."
        ),
    )
    parser.add_argument(
        "--resolve-canonical-root",
        action="store_true",
        help=(
            "Opt-in ancestor promotion: if ancestors include an ID from CONFLUENCE_CANONICAL_ROOT_IDS, "
            "use that page as enumeration root. Default is off (pasted page = root). "
            "Also set CONFLUENCE_RESOLVE_CANONICAL_ROOT=1 without this flag."
        ),
    )
    parser.add_argument(
        "--no-reuse-existing-by-root",
        action="store_true",
        help=(
            "Write under by-root/<enumeration-root>/ only (do not merge into an existing parent tree). "
            "Default: when pages/<id>.md already exists under another by-root/, reuse that directory."
        ),
    )
    parser.add_argument(
        "--enum-mode",
        choices=("bfs", "cql"),
        default=default_enum_mode(),
        help=(
            "How to build descendants-full.json: cql = CQL search + pagination (default); "
            "bfs = REST child/page listing. Override default with CONFLUENCE_ENUM_MODE=bfs|cql."
        ),
    )
    parser.add_argument(
        "--cql",
        default="",
        help=(
            "When --enum-mode cql: full CQL query. If empty, use CONFLUENCE_ENUMERATE_CQL or "
            'auto: space = "<key>" AND type = page AND (id = <root> OR ancestor = <root>) ORDER BY title.'
        ),
    )
    parser.add_argument(
        "--enum-page-size",
        type=int,
        default=None,
        metavar="N",
        help=(
            "Enumeration batch size 1-250: CQL search limit per request, or BFS child/list size. "
            "Default: CONFLUENCE_ENUMERATE_PAGE_SIZE or 250 (fewer round-trips than confluence_enumerate default 100)."
        ),
    )
    parser.add_argument(
        "--extract-workers",
        type=int,
        default=None,
        metavar="N",
        help=(
            "Extract step ThreadPoolExecutor size. Overrides CONFLUENCE_EXTRACT_WORKERS and "
            "auto workers derived from enumerated page count."
        ),
    )
    return parser


if __name__ == "__main__":
    main()
