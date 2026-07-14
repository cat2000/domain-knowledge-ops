# Install Domain Knowledge Ops skills

**Supported path: clone this repository and open the repo root in Cursor.**  
Demo fixtures, `.env.example`, `domain-knowledge/`, pipeline `scripts/`, rules, and contracts all live in the checkout. That is what newcomers and real work need.

Skills load from [`.cursor/skills/`](.cursor/skills/). Top-level [`skills/`](skills/) symlinks the same folders for discovery tools — that does **not** mean skill-only install is enough to run the product.

Pipeline **S1–S7**: [domain-knowledge-pipeline-contract.md](.cursor/contracts/domain-knowledge-pipeline-contract.md).

## Recommended: clone + open repo root (Cursor)

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

## What each path covers

| Need | Use |
|------|-----|
| Offline demo (`DEMO-1` / `DEMO-BILL-1`) | **Clone** + open repo root |
| Setup + Confluence → **S7** briefs | **Clone** + `.env` + `@setup-domain-ops` / `@generate-knowledge-from-wiki` |
| Story risk/split on real Jira | **Clone** with briefs under `domain-knowledge/curated/` (or fixtures for DEMO) |
| Jira history into Compose | **Clone** + `@add-knowledge-from-jira` |

## Optional: `npx skills` (limited — not for newcomers)

`npx skills add` only copies **skill markdown folders** into another project (often under `.agents/skills/`). It does **not** install:

- `.env.example`, `WALKTHROUGH.md`, product README
- `domain-knowledge/` (strategy, team-roots, **fixtures**)
- pipeline `scripts/`, `.cursor/rules/`, `.cursor/contracts/`, `_shared/`

So: **no reliable offline DEMO**, **no Path C**, broken relative links to rules/contracts. Do **not** recommend this as the install path in posts or onboarding.

Use only if you already maintain briefs/scripts in the target repo and want skill text copied in:

```bash
npx skills add cat2000/domain-knowledge-ops --list   # discovery / telemetry only

# Advanced — expect incomplete workspace; prefer clone instead
npx skills add cat2000/domain-knowledge-ops \
  --skill requirement-risk \
  --skill ticket-splitter \
  -a cursor -y
```

For anything beyond “skill files appeared,” **clone**.

## Other harnesses (Claude Code / Codex)

Still prefer a **full clone** as the workspace (or keep this repo checked out beside the app repo). Symlink or copy `.cursor/skills/<name>` only after fixtures/scripts/`.env` are available from the clone.

Skill-only copy into a harness directory has the **same gaps** as `npx skills` above.

## Complement, don’t replace

| Pack | Role |
|------|------|
| Superpowers / Spec Kit / general coding skills | How the agent **builds software** |
| **This pack** | How the agent **adjudicates domain truth** from Confluence/Jira for story review |

Use both: build with theirs; review stories against **S7** briefs from ours — from a **clone** of this repo.
