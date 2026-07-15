# Marketplace / distribution stub

Status: **public repo live** — https://github.com/cat2000/domain-knowledge-ops

Use this checklist for release polish and marketplace distribution.

## GitHub repository

- [x] Create public repo; push `main` with green CI — https://github.com/cat2000/domain-knowledge-ops
- [x] Replace `OWNER` placeholders with `cat2000`
- [x] Topics: `cursor`, `agent-skills`, `confluence`, `jira`, `domain-driven-design`, `atlassian`
- [x] Tag `v0.1.0` + GitHub Release — https://github.com/cat2000/domain-knowledge-ops/releases/tag/v0.1.0
- [x] Enable Discussions — https://github.com/cat2000/domain-knowledge-ops/discussions
- [x] About description updated (story risk / INVEST / test design / offline DEMO-1)

## Discovery vs install (important for posts)

**Onboarding in every post:** `git clone` → open repo root → `@requirement-risk DEMO-1 team=demo`.  
**Do not** present skill-folder copy tools as an install path ([INSTALL.md](../INSTALL.md)).

[agentskills.io](https://agentskills.io) is the **open skill format / spec**, not a submit portal. Top-level `skills/` exists so crawlers can find `SKILL.md` — not so newcomers skip cloning.

| Channel | Role | What we do |
|---------|------|------------|
| **GitHub clone** | **Only supported install** | README / Discussions / Release lead with clone |
| **Skill-format crawlers / skills.sh** | May index or rank public `SKILL.md` | Keep `skills/` + `SKILL.md` valid; never claim that equals product install |
| Optional registries | [skills.re](https://skills.re), [agentskillsource.com](https://agentskillsource.com) | Only if you want a second listing |

- [x] Docs: clone-only install; no npx install examples (INSTALL / README / HARNESS)
- [x] Document the four headline skills on the Release notes
- [ ] Optional: third-party registry submit — not required

## Cursor marketplace / plugin

Official path: [Cursor Plugins](https://cursor.com/docs/plugins) → package as `.cursor-plugin/plugin.json` → local test under `~/.cursor/plugins/local/` → submit at [cursor.com/marketplace/publish](https://cursor.com/marketplace/publish) (manual review).

**Decision (evaluate before building):**

| Keep clone-workspace (current) | Add Cursor plugin |
|--------------------------------|-------------------|
| Full pipeline needs `scripts/` + `.env` + `domain-knowledge/` | One-click skills for risk/split consumers |
| Offline DEMO-1 already works from repo root | Marketplace discoverability inside Cursor |
| Simpler SSOT | Plugin **cannot** ship secrets; S1 sync still needs a checkout |

Recommended evaluation order:

1. Spike: `.cursor-plugin/plugin.json` pointing at `skills/` (or symlinked headline four only)
2. Local load: `ln -s "$(pwd)" ~/.cursor/plugins/local/domain-knowledge-ops` → Reload Window → `@requirement-risk DEMO-1`
3. Decide: **skills-only plugin** (risk/split + setup) vs **defer** until someone installs without cloning
4. If yes: submit marketplace form; keep DEMO-1 as post-install aha; document that wiki Compose still needs the full repo

- [ ] Spike `.cursor-plugin/plugin.json` + local install smoke
- [ ] Go / no-go write-up in Discussions
- [ ] If go: submit [marketplace/publish](https://cursor.com/marketplace/publish); keep offline DEMO-1 as aha path

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
