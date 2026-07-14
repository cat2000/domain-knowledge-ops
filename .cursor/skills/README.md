# Cursor Skills · this repo

Three tracks: **build briefs** (Confluence → adjudicated domain knowledge) → **story risk** → **testable splits**. Same domain language across Jira tickets — not ad-hoc prompts.

**Language**: skill surfaces (`SKILL.md`, English `RUNBOOK.md`, CLI refs) are **English**. Chinese locales ship as `*.zh-CN.md` next to them. Process gloss: **confirm**, **continue**, **brief**. (zh-CN strings for these tokens live in `domain-knowledge/language/deliverable-locale-tokens.json`.)

**Human overview**: English product README [`../../README.md`](../../README.md) · Install: [`../../INSTALL.md`](../../INSTALL.md).

---

## 5-minute setup

No Marketplace plugin required. Clone, open the repo root in Cursor, `@` a skill.

### Offline first (no `.env`)

```text
@requirement-risk DEMO-1 team=demo
@ticket-splitter DEMO-1 team=demo
```

Fixture: [`../../domain-knowledge/fixtures/offline-demo/`](../../domain-knowledge/fixtures/offline-demo/).  
Paths A–C: [`../../WALKTHROUGH.md`](../../WALKTHROUGH.md). Install: [`../../INSTALL.md`](../../INSTALL.md).

### 1. Once (full pipeline)

| Step | Action |
|------|--------|
| Clone | `git clone <repo-url>`, open root in Cursor |
| Privacy | Cursor Settings → General → Privacy Mode (recommended) |
| Env | Root `.env`: `ATLASSIAN_EMAIL`, `ATLASSIAN_API_TOKEN`, `ATLASSIAN_BASE_URL`, `CONFLUENCE_BASE_URL` |
| Strategy | `@setup-domain-ops` — fill `strategy.md` §2, derive profiles, write **v3** `team-roots.json` |
| Teams | `domain-knowledge/jira/team-roots.json` — v3 `libraries` + `teams` mounts (template: `team-roots.example.json`) |
| Deps | `./scripts/setup.sh` for maintainers; skip for risk/split-only if briefs already exist |

### 2. Common `@` examples

**Build briefs**

```text
@generate-knowledge-from-wiki https://your-site.atlassian.net/wiki/spaces/DEMO/overview?homepageId=100001
```

(Use `libraries.<key>.confluence_overview` from your `team-roots.json`.)

**Story risk** (explicit `@` — not auto-loaded)

```text
@requirement-risk PROJ-123
```

Or: `@requirement-risk team=<your-team-key> PROJ-123` · optional `stage=pre_sprint focus=security`.

**Split**

```text
@ticket-splitter PROJ-123
```

**Jira into compose** (optional)

```text
@add-knowledge-from-jira team=<your-team-key> mode=history
```

---

## Skill index

| Skill | Trigger | Writes curated? |
|-------|---------|-----------------|
| [`setup-domain-ops`](setup-domain-ops/SKILL.md) | `@setup-domain-ops` | No (config only) |
| [`generate-knowledge-from-wiki`](generate-knowledge-from-wiki/SKILL.md) | `@…` + Confluence URL | Yes |
| [`distill-domain-knowledge`](distill-domain-knowledge/SKILL.md) | `@…` + root-id (advanced; default resume = **continue**) | Yes |
| [`add-knowledge-from-jira`](add-knowledge-from-jira/SKILL.md) | `@…` + team/mode | Yes (supplement) |
| [`requirement-risk`](requirement-risk/SKILL.md) | explicit `@` + KEY/text | No (read-only) |
| [`ticket-splitter`](ticket-splitter/SKILL.md) | explicit `@` + KEY | No (read-only) |

Runtime rules SSOT: `.cursor/rules/`. Contracts: `.cursor/contracts/`.

---

## vs Marketplace packs (e.g. Superpowers)

| | Marketplace | This repo |
|---|-------------|-----------|
| Install | Global plugin | Travels with the repo |
| Fit | General coding methodology | Confluence/Jira → domain briefs → story ops |
