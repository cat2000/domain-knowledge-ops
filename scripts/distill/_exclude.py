"""Shared path-prefix exclude helpers for distill gate scripts."""

from __future__ import annotations

from pathlib import Path


def load_exclude_prefixes(path: Path | None) -> list[str]:
    if path is None or not path.is_file():
        return []
    out: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if not s.endswith("/"):
            s = s + "/"
        out.append(s)
    return out


def is_excluded(rel_posix: str, prefixes: list[str]) -> bool:
    for p in prefixes:
        if rel_posix == p.rstrip("/") or rel_posix.startswith(p):
            return True
    return False
