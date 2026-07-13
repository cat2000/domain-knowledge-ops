"""Shared keyword-matching rules for wiki facet routing and Jira attribution."""

from __future__ import annotations

import re


def contains_classify_keyword(haystack: str, keyword: str) -> bool:
    """Title/body token match for keyword routing.

    Uses substring for most keys. For **investigation** only, uses a whole-word regex so
    Agile prose (*investigations*, *reinvestigation*) does not false-positive.
    """
    if keyword == "investigation":
        return bool(re.search(r"(?i)\binvestigation\b", haystack))
    return keyword in haystack
