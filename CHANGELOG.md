# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- [`docs/TEAM_ROOTS_V3.md`](docs/TEAM_ROOTS_V3.md) + [`team-roots.v3.example.json`](domain-knowledge/jira/team-roots.v3.example.json) — one Confluence **space** = one **library**; Jira teams mount `libraries[]` (multi-space compose deferred)
- `scripts/teams/team_roots_normalize.py` — load v2/v3 team-roots; flatten mounts for backward-compatible `team.root_id` / deliver maps

### Changed

- **Install narrative** — clone is the **only** supported install; removed `npx skills add` install examples (skill-folder copy is not an onboarding path; `skills/` kept for discovery only)
- **Path B** — with-vs-without brief contrast via [`docs/BENCHMARK.md`](docs/BENCHMARK.md) (not a same-output re-run of Path A)
- **`setup-domain-ops`** — slim dialogue; **writes v3** `team-roots.json` (`libraries` + team mounts)
- **Path C / TEAM_KNOWLEDGE_BASE** — single-library v3 onboarding; shipped `team-roots.json` + `team-roots.example.json` are v3
- **`teams/registry.py`** / **`jira_team_config`** — use normalized team-roots (v3-aware)

### Fixed

- Clarify offline demo tokens (`DEMO-1`, `DEMO-BILL-1`, `team=demo`) and `PROJ-123` placeholder in README / WALKTHROUGH / INSTALL
- Fix `TEAM_KNOWLEDGE_BASE.md` link to `team-roots.example.json`; update maintainer to `@cat2000`

## [0.1.0] - 2026-07-13

### Added

- **Skills pack** — Cursor-native skills under `.cursor/skills/` with `skills/` symlinks for `npx skills` discovery: `setup-domain-ops`, `generate-knowledge-from-wiki`, `distill-domain-knowledge`, `add-knowledge-from-jira`, `requirement-risk`, `ticket-splitter`
- **S1–S7 pipeline** — Ingest (S1) → Recognize (S2) → Compose (S3–S7) with human **confirm** / **continue** gates; **S7** locale briefs (`*-domain-brief.md`) as reader-facing deliverables
- **Confirm-gated Compose** — named methodology index in `docs/METHODOLOGY.md`
- **Offline demos** — `DEMO-1` (Acme Orders) + `DEMO-BILL-1` (Northwind Billing) fixtures
- **Locale tokens** — English-first deliverable labels; Classify `gap-scan.md` resolves via `deliverable_locale`
- **Scripts** — Confluence sync, Jira ingest/classify, domain gates, `verify_skills_pack.py`
- **Docs** — README, WALKTHROUGH, INSTALL, CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, BENCHMARK, HARNESS, MARKETPLACE, demo samples
- **CI** — GitHub Actions workflow: `verify_skills_pack.py` + unit tests on Python 3.12
- **Issue templates** — bug report + skill feedback

### Notes

- First public release targeting https://github.com/cat2000/domain-knowledge-ops
- `domain-knowledge/curated/` pipeline outputs remain gitignored; only fixtures ship in-repo.
- Tag `v0.1.0` only after the repository is public and CI is green on `main`.

[Unreleased]: https://github.com/cat2000/domain-knowledge-ops/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/cat2000/domain-knowledge-ops/releases/tag/v0.1.0
