# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **`@ticket-test-design`** — single-ticket release/Done test pack (must/should/later; given-AC→must coverage; Contract readiness vs Pack note; `automate` handoff tags). Rule: [`ticket_test_design.md`](.cursor/rules/ticket_test_design.md); gate: `scripts/jira/attachments/validate_ticket_test_design.py`; sample: [`docs/demo/ticket-test-design-DEMO-1.sample.md`](docs/demo/ticket-test-design-DEMO-1.sample.md)
- [`docs/TEAM_ROOTS_V3.md`](docs/TEAM_ROOTS_V3.md) + [`team-roots.v3.example.json`](domain-knowledge/jira/team-roots.v3.example.json) — one Confluence **space** = one **library**; Jira teams mount `libraries[]` (multi-space compose deferred)
- `scripts/teams/team_roots_normalize.py` — load v2/v3 team-roots; flatten mounts for backward-compatible `team.root_id` / deliver maps

### Changed

- **`@ticket-test-design` presentation** — optimize for ~60s start-testing (short Summary decision board; Must core fields; Design after Later; chat = draft GWT; AC as where+act+observe); golden `example-DEMO-1` slimmed accordingly
- **Install narrative** — clone is the **only** supported install; removed `npx skills add` install examples (skill-folder copy is not an onboarding path; `skills/` kept for discovery only)
- **Path B** — with-vs-without brief contrast via [`docs/BENCHMARK.md`](docs/BENCHMARK.md) (not a same-output re-run of Path A)
- **`setup-domain-ops`** — slim dialogue; **writes v3** `team-roots.json` (`libraries` + team mounts)
- **Path C / TEAM_KNOWLEDGE_BASE** — single-library v3 onboarding; shipped `team-roots.json` + `team-roots.example.json` are v3
- **`teams/registry.py`** / **`jira_team_config`** — use normalized team-roots (v3-aware)
- **Locale S7 path resolve** — `deliverable_locale.resolve_locale_brief_path` + `resolve_deliver_path` find zh-CN `*-领域知识定稿.md` even when map still lists `*-domain-brief.md`
- **`domain_profiles`** — v3 library `root_id` → mounting team
- **S2 checklist Note** — status + source-count aware; zero-source rows warn against confirm
- **requirement-risk validator** — accept English `Scope` / `Counts: MUST FIX …` variants
- **`tagging_acceptance.py`** — prep report (closure / Jira half / axis-landing essence / per-module confirm advice) + `--after-s3` exhaustiveness + `--after-s7 --strict` write-through gate (zero-rule fake coverage = FAIL); Path C / wiki skills require it before confirm and after S7
- **Axis landing & write-through** — [`industry-axis-remount.md`](.cursor/skills/generate-knowledge-from-wiki/references/industry-axis-remount.md): essence only (axes × land × write-through × confirm gates); no tenant product remount table in the pack (iron-laws 4d/4e)
- **Fail-closed Jira defaults** — no pack-default CMA theme/facet/proposition tables; checklist + `teams/<team>.json` only; removed WC epic / CBP keyword specials
- **Path C** — default Jira half when board exists; done = OK confirms + pending empty modules (not “all rows confirmed”); ban zero-rule confirmed S7
- Jira/wiki skill examples normalized to `team=demo` (zh-CN CLI/playbooks no longer teach `cma` / board 150)

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
