#!/usr/bin/env python3
"""
Fetch Jira Cloud issue attachments and (by default) issue comments via REST API
(Basic auth: email + API token).

Credentials: ATLASSIAN_* or JIRA_* in environment, or repo-root `.env` via runtime.atlassian_env.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
import urllib.error
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

_SCRIPTS = next(p for p in Path(__file__).resolve().parents if (p / "_install.py").is_file())
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
import _install

_install.bootstrap(__file__)

from runtime.atlassian_env import JiraEnv, load_dotenv

from jira.lib.jira_attachment_logic import (
    ISSUE_FIELDS,
    __version__,
    build_comments_digest,
    issue_brief_for_manifest,
)
from jira.lib.jira_fetch_http import fetch_issue_comments, http_bytes, http_json


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(
        description="Download Jira issue attachments; optionally fetch comments (Jira Cloud REST API v3)."
    )
    parser.add_argument("issue_key", help="e.g. DEV-12345")
    parser.add_argument(
        "--out",
        default="",
        help="Output directory (default: ./.jira_attachments/{ISSUE_KEY}/)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Also write issue.json (full issue payload from fields request) for inspection.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List attachment filenames and skip download.",
    )
    parser.add_argument(
        "--no-comments",
        action="store_true",
        help="Do not fetch issue comments (default: fetch and write comments.json).",
    )
    args = parser.parse_args()

    jira_env = JiraEnv.from_env(required=True)
    assert jira_env is not None
    auth = jira_env.auth_header()
    api_base = jira_env.api_base_url.rstrip("/")
    site_base = api_base[: -len("/rest/api/3")]

    key = args.issue_key.strip().upper()
    issue_url = (
        f"{api_base}/issue/{urllib.parse.quote(key)}"
        f"?{urllib.parse.urlencode([('fields', ISSUE_FIELDS)])}"
    )
    out_dir = args.out or os.path.join(".jira_attachments", key)
    os.makedirs(out_dir, exist_ok=True)

    start_epoch = time.time()
    started_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        data = http_json("GET", issue_url, auth)
    except SystemExit as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)

    if args.json and not args.dry_run:
        path = os.path.join(out_dir, "issue.json")
        atomic_write_text(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")
        print(f"Wrote {path}")

    comments_payload: dict | None = None
    comments_error: str | None = None
    if not args.no_comments and not args.dry_run:
        try:
            comments_payload = fetch_issue_comments(api_base, key, auth)
            comments_path = os.path.join(out_dir, "comments.json")
            atomic_write_text(
                comments_path,
                json.dumps(comments_payload, ensure_ascii=False, indent=2) + "\n",
            )
            comment_count = comments_payload.get("total", 0)
            print(f"Wrote {comments_path} ({comment_count} comment(s))")
            digest_path = os.path.join(out_dir, "comments_digest.txt")
            atomic_write_text(
                digest_path, build_comments_digest(key, comments_payload)
            )
            print(f"Wrote {digest_path}")
        except SystemExit as exc:
            comments_error = str(exc)
            print(f"Comments: {comments_error}", file=sys.stderr)
    elif not args.no_comments and args.dry_run:
        print("Would fetch comments -> comments.json + comments_digest.txt (same auth)")

    attachments = (data.get("fields") or {}).get("attachment") or []
    written_attachments: list[dict] = []
    if not attachments:
        print("No entries in fields.attachment (inline ADF media is not covered here).")
        print(
            f"Issue: {key}  summary: {(data.get('fields') or {}).get('summary', '')!r}"
        )

    for attachment in attachments:
        attachment_id = attachment.get("id")
        filename = attachment.get("filename") or f"attachment-{attachment_id}"
        content_url = attachment.get("content")
        if not content_url or attachment_id is None:
            print(f"Skip weird attachment record: {attachment!r}", file=sys.stderr)
            continue
        if args.dry_run:
            print(f"Would download: {filename!r}  id={attachment_id}")
            print(f"  {content_url}")
            written_attachments.append(
                {
                    "filename": filename,
                    "id": str(attachment_id),
                    "bytes": None,
                    "path": None,
                    "dry_run": True,
                }
            )
            continue
        download_url = f"{api_base}/attachment/content/{attachment_id}"
        try:
            body = http_bytes(download_url, auth)
        except SystemExit as exc:
            message = str(exc)
            print(f"Failed {filename}: {message}", file=sys.stderr)
            written_attachments.append(
                {
                    "filename": filename,
                    "id": str(attachment_id),
                    "error": message[:80],
                    "path": None,
                }
            )
            continue
        safe_name = filename.replace("/", "_").replace("..", "_")
        out_path = os.path.join(out_dir, safe_name)
        with open(out_path, "wb") as handle:
            handle.write(body)
        print(f"Wrote {out_path} ({len(body)} bytes)")
        written_attachments.append(
            {
                "filename": safe_name,
                "id": str(attachment_id),
                "bytes": len(body),
                "path": safe_name,
            }
        )

    if comments_payload and len(comments_payload.get("comments") or []) != int(
        comments_payload.get("total", -1)
    ):
        print(
            "Warning: comments total != len(comments) in payload (unexpected).",
            file=sys.stderr,
        )

    duration_ms = int((time.time() - start_epoch) * 1000)
    manifest: dict = {
        "script": "fetch_jira_attachments.py",
        "version": __version__,
        "issueKey": key,
        "jiraBaseUrl": site_base,
        "fetchedAt": started_iso,
        "durationMs": duration_ms,
        "options": {
            "json": args.json,
            "dryRun": args.dry_run,
            "noComments": args.no_comments,
        },
        "issueRequest": {"fields": ISSUE_FIELDS},
        "issue": issue_brief_for_manifest(data),
        "files": {
            "issueJson": "issue.json" if args.json and not args.dry_run else None,
            "commentsJson": "comments.json"
            if (comments_payload is not None and not args.dry_run)
            else None,
            "commentsDigest": "comments_digest.txt"
            if (comments_payload is not None and not args.dry_run)
            else None,
        },
        "comments": {
            "fetched": bool(comments_payload is not None),
            "count": (comments_payload or {}).get("total", 0)
            if comments_payload
            else 0,
            "error": comments_error,
        },
        "attachments": {
            "countInApi": len(attachments),
            "downloaded": written_attachments if not args.dry_run else written_attachments,
        },
    }
    manifest_path = os.path.join(out_dir, "fetch_manifest.json")
    if not args.dry_run:
        atomic_write_text(
            manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
        )
        print(f"Wrote {manifest_path}")
    else:
        print(
            f"Would write {manifest_path} (dry-run; not written)",
            file=sys.stderr,
        )


def atomic_write_text(path: str, text: str) -> None:
    atomic_write_bytes(path, text.encode("utf-8"))


def atomic_write_bytes(path: str, data: bytes) -> None:
    abspath = os.path.abspath(path)
    directory = os.path.dirname(abspath) or "."
    os.makedirs(directory, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".jira_fetch_", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
        os.replace(tmp, abspath)
    except Exception:
        if os.path.isfile(tmp):
            try:
                os.unlink(tmp)
            except OSError:
                pass
        raise


if __name__ == "__main__":
    main()
