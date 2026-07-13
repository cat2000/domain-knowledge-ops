# Marketplace / distribution stub

Status: **public repo live** — https://github.com/cat2000/domain-knowledge-ops

Use this checklist for release polish and marketplace distribution.

## GitHub repository

- [ ] Create public repo; push `main` with green CI
- [ ] Replace every `OWNER` placeholder (README badges, INSTALL, CHANGELOG links, issue templates)
- [ ] Topics: `cursor`, `agent-skills`, `confluence`, `jira`, `domain-driven-design`, `atlassian`
- [ ] Tag `v0.1.0` and publish a GitHub Release from [`CHANGELOG.md`](../CHANGELOG.md)
- [ ] Enable Discussions (Q&A + Show and tell)

## `npx skills` / agentskills.io

- [ ] Verify: `npx skills add cat2000/domain-knowledge-ops --list`
- [ ] Document the four headline skills on the Release notes
- [ ] Optional: submit listing to [agentskills.io](https://agentskills.io) when the catalog accepts external packs

## Cursor marketplace / plugin

- [ ] Evaluate packaging as a Cursor plugin (skills + thin bootstrap) vs clone-workspace model
- [ ] If plugin: one-command install mirroring Superpowers `/plugin-add` UX
- [ ] Keep offline DEMO-1 as the post-install aha path

## Launch narrative

Suggested one-liner for posts:

> Skills that teach agents to **keep domain truth** for story review — not just to ship code.

Link: README 60s demo + [`docs/BENCHMARK.md`](BENCHMARK.md) + [`docs/METHODOLOGY.md`](METHODOLOGY.md) (Confirm-gated Compose).

## Adoption signals (prefer over vanity stars)

| Signal | How to notice |
|--------|----------------|
| Fork filled `strategy.md` §2 | PR or discussion screenshot |
| `verify_skills_pack.py` green on fork CI | Badge / Actions |
| Second team key in `team-roots.json` | Config PR |
| DEMO-BILL-1 used in a write-up | Portability proof |
