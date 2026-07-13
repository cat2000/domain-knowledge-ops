# Multi-harness notes

Skills are authored under [`.cursor/skills/`](../.cursor/skills/) and mirrored via [`skills/`](../skills/) for installers that expect a top-level `skills/` tree.

## Cursor (primary)

1. Clone and open the **repo root** as the workspace.
2. Skills load from `.cursor/skills/` automatically.
3. Offline smoke: `@requirement-risk DEMO-1 team=demo`

## `npx skills` / agentskills-style

See [`INSTALL.md`](../INSTALL.md). Replace `cat2000/domain-knowledge-ops` after the repository is public.

```bash
npx skills add cat2000/domain-knowledge-ops --list
npx skills add cat2000/domain-knowledge-ops \
  --skill requirement-risk \
  --skill ticket-splitter \
  --skill setup-domain-ops \
  -a cursor -y
```

**Limitation:** wiki/Jira **S1** scripts live in this repo’s `scripts/` and need a checkout + `.env`. Skill-only install is enough for offline DEMO-* and for risk/split once briefs already exist on disk.

## Claude Code / Codex

1. Install headline skills into the harness skill directory (`npx skills … -a claude-code` / `-a codex`, or symlink `.cursor/skills/<name>`).
2. Keep a clone of this repo available when running Confluence sync or Jira ingest.
3. Prefer the same offline DEMO-1 smoke before wiring credentials.

## Expected smoke outputs

Recorded English samples (Cursor Agent chat style):

- [`docs/demo/requirement-risk-DEMO-1.sample.md`](demo/requirement-risk-DEMO-1.sample.md)
- [`docs/demo/ticket-splitter-DEMO-1.sample.md`](demo/ticket-splitter-DEMO-1.sample.md)

Harnesses may format markdown differently; validators under `scripts/jira/attachments/` accept English field headers when `--lang en` is used.
