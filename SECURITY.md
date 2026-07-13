# Security Policy

## Supported versions

Use the latest `main` branch (or a tagged release when published). Do not run untrusted forks against production Atlassian tenants without reviewing scripts.

## Credentials

- Store Atlassian credentials only in a local `.env` (see [`.env.example`](.env.example)). Never commit `.env`, API tokens, or personal access tokens.
- Prefer a dedicated bot account with least privilege: Confluence read on the wiki roots you sync; Jira read on the boards you ingest; attachment download only if you use attachment fetch.
- Set `ATLASSIAN_BASE_URL` / `CONFLUENCE_BASE_URL` explicitly. Do not rely on placeholder defaults in production.

## Reporting a vulnerability

**Please report security issues through [GitHub Security Advisories](https://github.com/cat2000/domain-knowledge-ops/security/advisories/new)** on this repository.

Include:

- Description and impact
- Steps to reproduce
- Affected paths or scripts (if known)

Do **not** attach live customer data, production wiki/Jira exports, or production tokens.

Maintainers are listed in [CONTRIBUTING.md](CONTRIBUTING.md). We aim to acknowledge reports within a few business days.

## Safe usage

- Treat `domain-knowledge/curated/`, `extracted/`, and `materialized/` as potentially sensitive local outputs — they are gitignored by default.
- Run `python3 scripts/verify_skills_pack.py` and the unit test suite before deploying forked changes to a shared tenant.
