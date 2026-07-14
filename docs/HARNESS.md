# Multi-harness notes

**Install: clone this repository and open the repo root.**  
Fixtures, `.env.example`, `domain-knowledge/`, `scripts/`, rules, and contracts travel with the checkout. Skills under [`.cursor/skills/`](../.cursor/skills/) (mirrored via [`skills/`](../skills/) for discovery) are not a standalone product.

## Cursor (primary)

1. Clone and open the **repo root** as the workspace.
2. Skills load from `.cursor/skills/` automatically.
3. Offline smoke: `@requirement-risk DEMO-1 team=demo`

## Claude Code / Codex

1. Open a **clone** of this repo (or keep it checked out next to the app).
2. Optionally symlink `.cursor/skills/<name>` into the harness skills directory **after** the clone provides fixtures/scripts.
3. Same offline smoke: `@requirement-risk DEMO-1 team=demo` from the clone workspace.

Skill-folder-only copies into another project are **not** supported (same gaps as omitting fixtures/scripts). See [`INSTALL.md`](../INSTALL.md).

## Expected smoke outputs

Recorded English samples (Cursor Agent chat style):

- [`docs/demo/requirement-risk-DEMO-1.sample.md`](demo/requirement-risk-DEMO-1.sample.md)
- [`docs/demo/ticket-splitter-DEMO-1.sample.md`](demo/ticket-splitter-DEMO-1.sample.md)

Harnesses may format markdown differently; validators under `scripts/jira/attachments/` accept English field headers when `--lang en` is used.
