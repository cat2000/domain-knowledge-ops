"""
Stored KB reader language vs extract-time translation.

**Default (recommended):** do **not** translate during Confluence extract.
`extracted/` / `materialized/` keep source wording (often English); **简体中文定稿**
is produced in **`curated/`** after Cursor (or HTTP distill) rewrites material.

**Legacy opt-in:** translate title/body during extract (slow on large trees):

  export CONFLUENCE_KB_TRANSLATE=1
  pip install deep-translator   # see scripts/requirements-kb.txt

Disable zh-oriented UI hints entirely:

  export CONFLUENCE_KB_OUTPUT_LANG=en

Classification still uses the original Confluence API title from JSON.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from typing import Optional, Tuple

_WARNED_MISSING = False
_WARNED_ERROR = False


def kb_translate_enabled() -> bool:
    """True only when explicitly opting into slow extract-time EN→zh translation."""
    if not kb_output_lang_zh():
        return False
    return os.environ.get("CONFLUENCE_KB_TRANSLATE", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def kb_output_lang_zh() -> bool:
    v = os.environ.get("CONFLUENCE_KB_OUTPUT_LANG", "zh").strip().lower()
    return v in ("zh", "zh-cn", "zh_cn", "cn")


def _cjk_ratio(s: str) -> float:
    if not s:
        return 0.0
    cjk = sum(1 for c in s if "\u4e00" <= c <= "\u9fff")
    return cjk / max(len(s), 1)


def _should_translate_block(s: str) -> bool:
    if not s.strip():
        return False
    if _cjk_ratio(s) >= 0.12:
        return False
    letters = sum(1 for c in s if "a" <= c.lower() <= "z")
    if letters < 10 and len(s.strip()) < 40:
        return False
    return letters >= 10


def _translator():
    try:
        from deep_translator import GoogleTranslator

        return GoogleTranslator(source="auto", target="zh-CN")
    except ImportError:
        return None


def _translate_one(translator, text: str) -> str:
    global _WARNED_MISSING, _WARNED_ERROR
    if not text.strip():
        return text
    if translator is None:
        if not _WARNED_MISSING:
            print(
                "confluence_kb_zh_display: 已设置 CONFLUENCE_KB_TRANSLATE=1 但未安装 deep-translator；"
                "请在仓库根执行: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt",
                file=sys.stderr,
            )
            _WARNED_MISSING = True
        return text
    try:
        return translator.translate(text)
    except Exception as e:
        if not _WARNED_ERROR:
            print(
                f"confluence_kb_zh_display: 翻译失败（{e}），保留原文。",
                file=sys.stderr,
            )
            _WARNED_ERROR = True
        return text


def _translate_long(translator, text: str) -> str:
    if not text.strip():
        return text
    max_chunk = 4200
    if len(text) <= max_chunk:
        return _translate_one(translator, text)
    out: list[str] = []
    i = 0
    while i < len(text):
        chunk = text[i : i + max_chunk]
        out.append(_translate_one(translator, chunk))
        i += max_chunk
        time.sleep(0.06)
    return "".join(out)


def ensure_zh_display(text: str) -> str:
    """Localize page body for KB readers (zh-CN by default)."""
    if not kb_translate_enabled() or not text.strip():
        return text
    if text.startswith("[提取失败]"):
        return text
    translator = _translator()
    blocks = re.split(r"\n\s*\n", text)
    done: list[str] = []
    for b in blocks:
        b = b.strip()
        if not b:
            continue
        if _should_translate_block(b):
            done.append(_translate_long(translator, b))
            time.sleep(0.05)
        else:
            done.append(b)
    return "\n\n".join(done).strip()


def maybe_zh_title(title: str) -> Tuple[str, Optional[str]]:
    """Returns (display_title, confluence_title_if_translated)."""
    if not kb_translate_enabled() or not title.strip():
        return title, None
    if _cjk_ratio(title) >= 0.22:
        return title, None
    translator = _translator()
    zh = _translate_one(translator, title.strip())
    time.sleep(0.04)
    if zh != title:
        return zh, title
    return title, None


def parse_title_from_extract_file(raw: str) -> Optional[str]:
    """Read `title:` from YAML front matter of a per-page extract."""
    if not raw.startswith("---\n"):
        return None
    end = raw.find("\n---\n", 4)
    if end == -1:
        return None
    fm = raw[4:end]
    for line in fm.splitlines():
        if not line.startswith("title:"):
            continue
        val = line[len("title:") :].strip()
        if val.startswith('"') or val.startswith("'"):
            try:
                return json.loads(val)
            except json.JSONDecodeError:
                return val.strip('"').strip("'")
        return val
    return None
