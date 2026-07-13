"""Display labels for known demo root pages (optional; not implicit team roots)."""

from __future__ import annotations

from runtime.atlassian_env import DEFAULT_ATLASSIAN_SITE, DEFAULT_CONFLUENCE_BASE

KNOWN_ROOT_LABELS: dict[str, tuple[str, str]] = {
    "48696506": (
        "Demo App B",
        f"{DEFAULT_CONFLUENCE_BASE}/spaces/ALPHA/pages/48696506/Demo+App+B",
    ),
    "48694645": (
        "Demo App A",
        f"{DEFAULT_CONFLUENCE_BASE}/spaces/ALPHA/pages/48694645/Demo+App+A",
    ),
}


def default_root_label_url(page_id: str, url_arg: str | None) -> tuple[str, str]:
    """Return (label, url) for coverage/extract README."""
    if url_arg and url_arg.strip().startswith("http"):
        url = url_arg.strip()
        if page_id in KNOWN_ROOT_LABELS:
            label = KNOWN_ROOT_LABELS[page_id][0]
        else:
            label = f"Root {page_id}"
        return (label, url)
    if page_id in KNOWN_ROOT_LABELS:
        return KNOWN_ROOT_LABELS[page_id]
    return (
        f"Root {page_id}",
        f"{DEFAULT_ATLASSIAN_SITE}/wiki/pages/viewpage.action?pageId={page_id}",
    )
