# Install Domain Knowledge Ops skills

Skills live in [`.cursor/skills/`](.cursor/skills/) (Cursor-native). Top-level [`skills/`](skills/) symlinks the same folders so [`npx skills`](https://github.com/vercel-labs/skills) / [agentskills.io](https://agentskills.io) installers can discover them.

Pipeline steps referenced here use **S1–S7** (Ingest → Recognize → Compose through locale briefs). See [`.cursor/contracts/domain-knowledge-pipeline-contract.md`](.cursor/contracts/domain-knowledge-pipeline-contract.md).

## Fastest path (Cursor)

```bash
git clone https://github.com/cat2000/domain-knowledge-ops.git
cd domain-knowledge-ops
python3 scripts/verify_skills_pack.py   # offline layout check (CI runs the same)
# Open this folder as the Cursor **workspace root** (File → Open Folder on the repo root).
# Skills load from `.cursor/skills/` only when the workspace root is this clone.
```

Then try the offline demo (no Atlassian). **`DEMO-1`** is a **fake issue key** shipped under [`domain-knowledge/fixtures/offline-demo/`](domain-knowledge/fixtures/offline-demo/) (Acme Orders amend story); **`team=demo`** is the sample team. `DEMO-*` skips live Jira.

```text
@requirement-risk DEMO-1 team=demo
```

Walkthrough (explains tokens): [`WALKTHROUGH.md`](WALKTHROUGH.md).

## Via `npx skills` (multi-agent)

Local path install (from a clone):

```bash
npx skills add ./path/to/domain-knowledge-ops --list
```

From the public repo:

```bash
# List installable skills
npx skills add cat2000/domain-knowledge-ops --list

# Headline skills into the current project (Cursor + others)
npx skills add cat2000/domain-knowledge-ops \
  --skill requirement-risk \
  --skill ticket-splitter \
  --skill setup-domain-ops \
  --skill generate-knowledge-from-wiki \
  -a cursor -y

# Optional: Claude Code / Codex
npx skills add cat2000/domain-knowledge-ops --skill requirement-risk -a claude-code -a codex -y
```

From a local checkout:

```bash
npx skills add ./path/to/domain-knowledge-ops --all -a cursor -y
```

**Note:** Full wiki sync (**S1–S7**) still needs this repo’s `scripts/` + `.env` (Confluence). Skill-only install is enough for offline fixtures and for risk/split once **S7** briefs exist.

## Claude Code plugin-style

1. Add this repository as a skill source, **or** copy/symlink `.cursor/skills/<name>` into your Claude skills directory.
2. Prefer installing at least: `setup-domain-ops`, `generate-knowledge-from-wiki`, `requirement-risk`, `ticket-splitter`.
3. Keep the Python pipeline in-repo when running **S1–S7** (scripts are not bundled inside each skill folder).

## What each install path covers

| Need | Minimum install |
|------|-----------------|
| Offline demo (`DEMO-1`) | Open repo in Cursor |
| Story risk/split on existing briefs | `requirement-risk`, `ticket-splitter` |
| Full Confluence → **S7** briefs | Repo + `.env` + `generate-knowledge-from-wiki` (+ `setup-domain-ops` first time) |
| Jira history into same Compose path | `add-knowledge-from-jira` + wiki Recognize/Compose |

## Complement, don’t replace

| Pack | Role |
|------|------|
| Superpowers / Spec Kit / general coding skills | How the agent **builds software** |
| **This pack** | How the agent **adjudicates domain truth** from Confluence/Jira for story review |

Use both: build with theirs; review stories against **S7** briefs from ours.
