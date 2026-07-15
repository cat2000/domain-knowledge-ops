# domain-knowledge/

Landing zone for domain knowledge: Confluence → `extracted/` / `materialized/` → Cursor distill → `curated/` (read `_deliver/…定稿.md`).

**Source of truth is Confluence** (and Jira for ticket evidence). Fix business text in the source systems, then re-sync.

**Strategy-first**: fill [`strategy.md`](strategy.md) §2 with Cursor (`@setup-domain-ops`), then derive `s2-domain-profiles.json`. The repo ships an **empty** module shell — not a default industry cut.

---

## Where to start

| You are… | Start here |
|----------|------------|
| First-time setup | `@setup-domain-ops` → fill strategy → derive profiles |
| Offline demo (no Atlassian) | [`fixtures/offline-demo/`](fixtures/offline-demo/) → `@requirement-risk` / `@ticket-splitter` / `@ticket-test-design DEMO-1` |
| Story reviewer | [`TEAM_KNOWLEDGE_BASE.md`](../TEAM_KNOWLEDGE_BASE.md) |
| Methodology template | [`strategy.md`](strategy.md) · fictional fill example [`strategy.example.md`](strategy.example.md) |
| Wiki distill | `@generate-knowledge-from-wiki` → [RUNBOOK](../.cursor/skills/generate-knowledge-from-wiki/RUNBOOK.md) |
| Jira supplement | `@add-knowledge-from-jira` → [`jira/README.md`](jira/README.md) |
| Skills index | [`.cursor/skills/README.md`](../.cursor/skills/README.md) |
| English product README | [`../README.md`](../README.md) |

---

## Files (SSOT)

**Language**: English is the default for methodology/contracts below. Chinese locales ship as `*.zh-CN.md` beside them. Deliverable section/status labels (en ↔ zh-CN): [`language/deliverable-locale-tokens.json`](language/deliverable-locale-tokens.json) — English docs cite English labels only; agents emit mapped strings for `defaults.deliverable_locale`.

| Path | Purpose |
|------|---------|
| `strategy.md` | Methodology + **fill-in** industry context (§2) — human SSOT · [`strategy.zh-CN.md`](strategy.zh-CN.md) |
| `strategy.example.md` | Fictional filled §2 (format only) · [`strategy.example.zh-CN.md`](strategy.example.zh-CN.md) |
| `s2-domain-profiles.json` | Machine themes/facets — **derived from strategy**, empty until then |
| `s2-propose-industry-seeds.json` | Propose seeds — empty `module_seeds` until derived |
| `distill-quality-bar.md` | Compose quality bar (S4–S7) · [`distill-quality-bar.zh-CN.md`](distill-quality-bar.zh-CN.md) |
| `distill-authoring-contract.md` | S5–S7 authoring contract · [`distill-authoring-contract.zh-CN.md`](distill-authoring-contract.zh-CN.md) |
| `distill-document-skeleton.md` | S4/S5 skeleton · [`distill-document-skeleton.zh-CN.md`](distill-document-skeleton.zh-CN.md) |
| `DOMAIN_MODULE_CHECKLIST.template.md` | Checklist layout · [`DOMAIN_MODULE_CHECKLIST.template.zh-CN.md`](DOMAIN_MODULE_CHECKLIST.template.zh-CN.md) |
| `language/glossary.md` | Glossary (project-specific) |
| `jira/team-roots.json` | v3: libraries (spaces) + teams (boards + mounts) |
| `jira/team-roots.example.json` | Path C single-library template |
| `jira/team-roots.v3.example.json` | Multi-mount illustration only |
| `jira/teams/*.json` | Per-team classify facets (fill after strategy) |

---

## Generated dirs (local only; empty in public tree)

| Dir | Writer | Notes |
|-----|--------|-------|
| `extracted/by-root/<root>/` | S1 scripts | extracts |
| `materialized/by-root/<root>/` | S1 scripts | review source set |
| `curated/by-root/<root>/` | Cursor S2–S7 | checklist, aggregates, `_deliver/` |

S1 sync CLI: `python3 scripts/sync_domain_knowledge_from_confluence.py --url …` (see `scripts/README.md`).

Configure teams in [`jira/team-roots.json`](jira/team-roots.json). Do not commit production tenant exports to a public fork.
