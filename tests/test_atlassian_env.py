#!/usr/bin/env python3
"""Unit tests for runtime/atlassian_env.py."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.contract_support import ensure_scripts_on_path

ensure_scripts_on_path()

from runtime.atlassian_env import (  # noqa: E402
    AtlassianCredentials,
    ConfluenceEnv,
    JiraEnv,
    atlassian_auth_header,
    credentials_from_env,
    load_dotenv,
    wiki_api_base,
)


class TestAtlassianCredentials(unittest.TestCase):
    def test_auth_header_is_basic(self) -> None:
        creds = AtlassianCredentials(email="a@b.com", api_token="tok")
        self.assertTrue(creds.auth_header().startswith("Basic "))


class TestLoadDotenv(unittest.TestCase):
    def test_loads_without_overriding_existing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env_file = Path(tmp) / ".env"
            env_file.write_text('ATLASSIAN_EMAIL=new@x.com\nFOO=bar\n', encoding="utf-8")
            with mock.patch.dict(os.environ, {"ATLASSIAN_EMAIL": "keep@x.com"}, clear=False):
                with mock.patch("os.getcwd", return_value=tmp):
                    load_dotenv()
                self.assertEqual(os.environ["ATLASSIAN_EMAIL"], "keep@x.com")
                self.assertEqual(os.environ["FOO"], "bar")


class TestCredentialsFromEnv(unittest.TestCase):
    def test_missing_raises_when_required(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(SystemExit):
                credentials_from_env(required=True)

    def test_returns_none_when_optional(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(credentials_from_env(required=False))

    def test_jira_email_alias_fallback(self) -> None:
        with mock.patch.dict(
            os.environ,
            {"JIRA_EMAIL": "j@x.com", "JIRA_API_TOKEN": "tok"},
            clear=True,
        ):
            creds = credentials_from_env(required=True)
            assert creds is not None
            self.assertEqual(creds.email, "j@x.com")
            self.assertEqual(creds.api_token, "tok")


class TestServiceEnvs(unittest.TestCase):
    def test_jira_api_base_strips_wiki_suffix(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "ATLASSIAN_EMAIL": "a@b.com",
                "ATLASSIAN_API_TOKEN": "t",
                "ATLASSIAN_BASE_URL": "https://x.atlassian.net/wiki",
            },
            clear=True,
        ):
            env = JiraEnv.from_env()
            assert env is not None
            self.assertEqual(env.api_base_url, "https://x.atlassian.net/rest/api/3")

    def test_confluence_from_env(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "ATLASSIAN_EMAIL": "a@b.com",
                "ATLASSIAN_API_TOKEN": "t",
                "CONFLUENCE_BASE_URL": "https://x.atlassian.net/wiki",
            },
            clear=True,
        ):
            env = ConfluenceEnv.from_env()
            assert env is not None
            self.assertEqual(env.wiki_base_url, "https://x.atlassian.net/wiki")
            self.assertEqual(env.auth_header(), atlassian_auth_header())

    def test_wiki_api_base_appends_wiki(self) -> None:
        with mock.patch.dict(
            os.environ, {"ATLASSIAN_BASE_URL": "https://x.atlassian.net"}, clear=True
        ):
            self.assertEqual(wiki_api_base(), "https://x.atlassian.net/wiki")


if __name__ == "__main__":
    unittest.main()
