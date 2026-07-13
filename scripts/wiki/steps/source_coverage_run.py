"""Source coverage markdown — orchestration and disk I/O."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from wiki.lib.source_coverage_logic import render_source_coverage_markdown


def load_classify(script_path: Path):
    spec = importlib.util.spec_from_file_location("cov_dyn", script_path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod.classify


def run_source_coverage(
    *,
    json_path: Path,
    out_path: Path,
    classify_module: Path,
    root_page_id: str,
    root_url: str,
    root_label: str = "",
    pages_dir: Path | None = None,
) -> int:
    rows = json.loads(json_path.read_text(encoding="utf-8"))
    classify = load_classify(classify_module)
    markdown = render_source_coverage_markdown(
        rows,
        classify=classify,
        root_page_id=root_page_id,
        root_url=root_url,
        root_label=root_label,
        pages_dir=pages_dir,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(markdown, encoding="utf-8")
    print(f"Wrote {out_path} ({len(rows)} rows)", file=sys.stderr)
    return 0
