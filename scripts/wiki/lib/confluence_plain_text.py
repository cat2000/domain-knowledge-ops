"""
Shared Confluence HTML/storage → readable plain text helpers for KB extraction.

Removes common Cloud noise (e.g. leaked [data-colorid=…] fragments), preserves
paragraphs/list breaks where possible.
"""

from __future__ import annotations

import re
from html import unescape
from html.parser import HTMLParser


_BLOCK_TAGS = frozenset(
    {
        "p",
        "div",
        "li",
        "tr",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "table",
        "thead",
        "tbody",
        "ul",
        "ol",
        "section",
        "article",
    }
)


def clean_leaked_markup_tokens(text: str) -> str:
    """Strip fragments sometimes left in exported/plain text (Atlassian color tokens, etc.)."""
    if not text:
        return ""
    s = text
    # Repeated ADL / Fabric UI color annotations leaked as plain text
    s = re.sub(r"\[data-colorid=[^\]]+\]\{[^}]*\}", "", s)
    s = re.sub(r"html\[data-color-mode=[^\]]+\]\s*", "", s)
    s = re.sub(r"html\[data-color-mode=[^\]]+\]\s*\[data-colorid=[^\]]+\]\{[^}]*\}", "", s)
    # Legacy bracket noise
    s = re.sub(r"\{color:[^}]+\}", "", s)
    return s


def normalize_document(text: str) -> str:
    """Collapse excessive blank lines; trim line ends (single blank between blocks)."""
    if not text:
        return ""
    lines = [ln.rstrip() for ln in text.splitlines()]
    out: list[str] = []
    blank_run = 0
    for ln in lines:
        if not ln.strip():
            blank_run += 1
            if blank_run <= 1:
                out.append("")
        else:
            blank_run = 0
            out.append(ln.strip())
    return "\n".join(out).strip()


def _preprocess_html(html: str) -> str:
    if not html:
        return ""
    h = html
    h = re.sub(r"(?is)<script[^>]*>.*?</script>", "", h)
    h = re.sub(r"(?is)<style[^>]*>.*?</style>", "", h)
    # Block boundaries → newlines before tag stripping
    h = re.sub(r"(?i)</p>\s*<p\b[^>]*>", "\n\n", h)
    h = re.sub(r"(?i)<br\s*/?>", "\n", h)
    h = re.sub(r"(?i)</div>\s*<div\b[^>]*>", "\n\n", h)
    h = re.sub(r"(?i)</li>\s*<li\b[^>]*>", "\n", h)
    h = re.sub(r"(?i)</tr>\s*<tr\b[^>]*>", "\n", h)
    return h


class _HtmlToText(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        t = tag.lower()
        if t == "br":
            self._parts.append("\n")
        elif t in _BLOCK_TAGS:
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        t = tag.lower()
        if t in _BLOCK_TAGS and t != "br":
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        if data:
            self._parts.append(data)


def html_to_readable_plain(html: str) -> str:
    if not html or not html.strip():
        return ""
    html = _preprocess_html(html)
    p = _HtmlToText()
    try:
        p.feed(html)
        p.close()
    except Exception:
        t = re.sub(r"<[^>]+>", " ", html)
        t = unescape(t)
        t = re.sub(r"[ \t\r\f\v]+", " ", t)
        t = clean_leaked_markup_tokens(t)
        return normalize_document(t)
    raw = "".join(p._parts)
    t = unescape(raw)
    t = re.sub(r"[ \t\r\f\v]+", " ", t)
    t = re.sub(r" *\n *", "\n", t)
    t = clean_leaked_markup_tokens(t)
    return normalize_document(t)


def storage_xml_to_readable_plain(storage_xml: str) -> str:
    """Prefer paragraph/table breaks from storage before stripping tags."""
    if not storage_xml:
        return ""
    t = storage_xml
    t = re.sub(r"(?is)<script[^>]*>.*?</script>", "", t)
    t = re.sub(r"(?is)<style[^>]*>.*?</style>", "", t)
    t = re.sub(r"(?i)</p>\s*<p\b[^>]*>", "\n\n", t)
    t = re.sub(r"(?i)<br\s*/?>", "\n", t)
    t = re.sub(r"(?i)</li>\s*<li\b[^>]*>", "\n", t)
    t = re.sub(r"(?i)</tr>\s*<tr\b[^>]*>", "\n", t)
    t = re.sub(r"<[^>]+>", " ", t)
    t = unescape(t)
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r" *\n *", "\n", t)
    t = clean_leaked_markup_tokens(t)
    return normalize_document(t)
