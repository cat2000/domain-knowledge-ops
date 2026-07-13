# Contributing to Domain Knowledge Ops

Thank you for helping improve agent skills, scripts, and docs for enterprise domain truth workflows.

## Maintainers

- **[@cat2000](https://github.com/cat2000)** — primary maintainer for this public repository

For security reports, use [GitHub Security Advisories](SECURITY.md) instead of public issues.

## Development setup

```bash
git clone https://github.com/cat2000/domain-knowledge-ops.git
cd domain-knowledge-ops
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
./scripts/setup.sh            # optional convenience wrapper
```

Copy [`.env.example`](.env.example) to `.env` for Atlassian integration tests — **never commit `.env`**.

## Running tests

From repo root:

```bash
# Layout + symlink contract (same as CI)
python3 scripts/verify_skills_pack.py

# Full unit suite
python3 -m unittest discover -s tests -p 'test_*.py'
```

CI runs both on every push/PR (see [`.github/workflows/ci.yml`](.github/workflows/ci.yml)).

Targeted examples:

```bash
python3 -m unittest tests.test_offline_demo_and_install -v
python3 -m unittest tests.test_skills_layout -v
python3 -m unittest tests.test_pipeline_s_steps -v
```

## Pull request expectations

1. **Scope** — One logical change per PR when possible (skill behavior, script gate, or docs — not all three unless tightly coupled).
2. **Tests** — Add or update unit tests for script/gate behavior. Doc-only PRs should not break `verify_skills_pack.py` or naming contracts in `tests/`.
3. **Pipeline accuracy** — Use **S1–S7** step IDs and narrative stages (Ingest / Recognize / Compose) consistently with [`.cursor/contracts/domain-knowledge-pipeline-contract.md`](.cursor/contracts/domain-knowledge-pipeline-contract.md).
4. **No secrets** — No tokens, tenant URLs with credentials, or production wiki/Jira dumps in commits.
5. **Offline demo** — Changes to `domain-knowledge/fixtures/offline-demo/` must keep `DEMO-1` runnable without network.
6. **Description** — Explain *why* the change matters for story review or pipeline gates, not only *what* files changed.

## Language SSOT (English + locales)

| Layer | Rule |
|-------|------|
| **English SSOT** | `SKILL.md`, `RUNBOOK.md`, CLI refs, root docs, `.cursor/rules/*.md` (non-locale) |
| **Locales** | Ship `*.zh-CN.md` **next to** the English file; do not inline large zh-CN blocks in English SSOT |
| **Process tokens** | English docs: `confirm`, `continue`, `brief`, `confirmed` — mapped per locale in [`domain-knowledge/language/deliverable-locale-tokens.json`](domain-knowledge/language/deliverable-locale-tokens.json) |
| **Deliverables** | **S6** `*-source-brief.md` (source language) · **S7** `*-domain-brief.md` (locale reader doc) |
| **Root README paths** | No CJK characters in English doc paths or filenames |

When updating behavior, update English SSOT first, then mirror critical sections in `*.zh-CN.md` if the locale surface changed.

## Skills pack layout

- Canonical skills: [`.cursor/skills/<name>/`](.cursor/skills/)
- Discovery symlinks: [`skills/<name>/`](skills/) → must stay in sync (enforced by `verify_skills_pack.py`)
- Runtime rules: [`.cursor/rules/`](.cursor/rules/)
- Contracts: [`.cursor/contracts/`](.cursor/contracts/)

## Issue templates

Use the GitHub templates for bugs and skill feedback. Include:

- Skill name and `@` invocation used
- Expected vs actual output (or gate error)
- Whether offline `DEMO-1` reproduces the issue

## Code of conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md). Be respectful; assume good intent.

## License

By contributing, you agree that your contributions are licensed under the [MIT License](LICENSE).
