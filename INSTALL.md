# Install Domain Knowledge Ops skills

**Only supported path: clone this repository and open the repo root in Cursor.**

Demo fixtures, `.env.example`, `domain-knowledge/`, pipeline `scripts/`, rules, and contracts all live in the checkout. That is what newcomers and real work need.

Skills load from [`.cursor/skills/`](.cursor/skills/). Top-level [`skills/`](skills/) mirrors the same folders so skill-format crawlers can discover `SKILL.md` files — **discovery plumbing, not a second install method**.

Pipeline **S1–S7**: [domain-knowledge-pipeline-contract.md](.cursor/contracts/domain-knowledge-pipeline-contract.md).

## Clone + open repo root (Cursor)

```bash
git clone https://github.com/cat2000/domain-knowledge-ops.git
cd domain-knowledge-ops
python3 scripts/verify_skills_pack.py   # offline layout check (CI runs the same)
# File → Open Folder on this repo root (not a subfolder).
```

Offline demo (no Atlassian). **`DEMO-1`** is a shipped fake key under [`domain-knowledge/fixtures/offline-demo/`](domain-knowledge/fixtures/offline-demo/); **`team=demo`** is the sample team. `DEMO-*` skips live Jira.

```text
@requirement-risk DEMO-1 team=demo
@ticket-splitter DEMO-1 team=demo
```

Real tenant (credentials): copy [`.env.example`](.env.example) → `.env`, then [WALKTHROUGH.md](WALKTHROUGH.md) **Path C**.

## What you get from a clone

| Need | Use |
|------|-----|
| Offline demo (`DEMO-1` / `DEMO-BILL-1`) | Open repo root → `@requirement-risk` / `@ticket-splitter` |
| Setup + Confluence → **S7** briefs | `.env` + `@setup-domain-ops` / `@generate-knowledge-from-wiki` |
| Story risk/split on real Jira | Briefs under `domain-knowledge/curated/` (or fixtures for DEMO) |
| Jira history into Compose | `@add-knowledge-from-jira` |

## Not an install path

Tools that only copy skill folders into another project (for example `npx skills add`) **omit** fixtures, `.env.example`, scripts, rules, and contracts. They are **not** a supported way to run this pack. Do not use them in posts or onboarding. Keep using **clone**.

## Other harnesses (Claude Code / Codex)

Open a **full clone** as the workspace (or keep this repo checked out beside the app). Symlink `.cursor/skills/<name>` only if the clone already provides fixtures and scripts.

## Complement, don’t replace

| Pack | Role |
|------|------|
| Superpowers / Spec Kit / general coding skills | How the agent **builds software** |
| **This pack** | How the agent **adjudicates domain truth** from Confluence/Jira for story review |

Use both: build with theirs; review stories against **S7** briefs from ours — from a **clone** of this repo.
