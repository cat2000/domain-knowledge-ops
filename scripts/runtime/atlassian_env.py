"""Atlassian credentials and service URLs (SSOT — no jira/wiki business imports)."""

from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from typing import Optional

# Placeholder only — real site must come from env / .env for production use.
DEFAULT_ATLASSIAN_SITE = "https://your-site.atlassian.net"
DEFAULT_CONFLUENCE_BASE = f"{DEFAULT_ATLASSIAN_SITE}/wiki"


def load_dotenv() -> None:
    """Load repo ``.env`` into ``os.environ`` (does not override existing keys)."""
    path = (os.environ.get("CONFLUENCE_ENV_FILE") or "").strip()
    if not path:
        cur = os.path.abspath(os.getcwd())
        for _ in range(8):
            candidate = os.path.join(cur, ".env")
            if os.path.isfile(candidate):
                path = candidate
                break
            parent = os.path.dirname(cur)
            if parent == cur:
                break
            cur = parent
    if not path or not os.path.isfile(path):
        return
    with open(path, encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val


@dataclass(frozen=True)
class AtlassianCredentials:
    email: str
    api_token: str

    def auth_header(self) -> str:
        raw = f"{self.email}:{self.api_token}".encode()
        return "Basic " + base64.b64encode(raw).decode("ascii")


def credentials_from_env(*, required: bool = True) -> Optional[AtlassianCredentials]:
    email = (
        os.environ.get("ATLASSIAN_EMAIL", "").strip()
        or os.environ.get("JIRA_EMAIL", "").strip()
    )
    token = (
        os.environ.get("ATLASSIAN_API_TOKEN", "").strip()
        or os.environ.get("JIRA_API_TOKEN", "").strip()
    )
    if not email or not token:
        if required:
            raise SystemExit(
                "Set ATLASSIAN_EMAIL and ATLASSIAN_API_TOKEN (or repo .env) for Atlassian REST."
            )
        return None
    return AtlassianCredentials(email=email, api_token=token)


def atlassian_auth_header() -> str:
    creds = credentials_from_env(required=True)
    assert creds is not None
    return creds.auth_header()


@dataclass(frozen=True)
class ConfluenceEnv:
    wiki_base_url: str
    credentials: AtlassianCredentials

    @classmethod
    def from_env(cls, *, required: bool = True) -> Optional[ConfluenceEnv]:
        creds = credentials_from_env(required=required)
        if creds is None:
            return None
        wiki = os.environ.get("CONFLUENCE_BASE_URL", DEFAULT_CONFLUENCE_BASE).strip()
        return cls(wiki_base_url=wiki, credentials=creds)

    def auth_header(self) -> str:
        return self.credentials.auth_header()


@dataclass(frozen=True)
class JiraEnv:
    api_base_url: str
    credentials: AtlassianCredentials

    @classmethod
    def from_env(cls, *, required: bool = True) -> Optional[JiraEnv]:
        creds = credentials_from_env(required=required)
        if creds is None:
            return None
        base = (
            os.environ.get("ATLASSIAN_BASE_URL", "").strip()
            or os.environ.get("JIRA_BASE_URL", "").strip()
            or os.environ.get("CONFLUENCE_BASE_URL", "").strip()
        )
        if not base:
            base = DEFAULT_ATLASSIAN_SITE
        base = base.rstrip("/")
        if base.endswith("/wiki"):
            base = base[: -len("/wiki")]
        return cls(api_base_url=f"{base}/rest/api/3", credentials=creds)

    def auth_header(self) -> str:
        return self.credentials.auth_header()


def site_base_url() -> str:
    """Atlassian site root (no ``/wiki``), from env or placeholder."""
    base = (
        os.environ.get("ATLASSIAN_BASE_URL", "").strip()
        or os.environ.get("JIRA_BASE_URL", "").strip()
        or os.environ.get("CONFLUENCE_BASE_URL", "").strip()
        or DEFAULT_ATLASSIAN_SITE
    )
    base = base.rstrip("/")
    if base.endswith("/wiki"):
        base = base[: -len("/wiki")]
    return base


def jira_browse_base() -> str:
    """Base URL for human-facing ``/browse/<KEY>`` links."""
    return site_base_url()


def wiki_api_base() -> str:
    """Confluence REST base including ``/wiki``."""
    base = site_base_url()
    return base + "/wiki"


def jira_api_base() -> str:
    """Jira REST API v3 base URL."""
    env = JiraEnv.from_env(required=True)
    assert env is not None
    return env.api_base_url
