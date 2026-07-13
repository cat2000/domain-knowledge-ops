---
name: setup-domain-ops
description: >-
  One-time setup: Atlassian site, team roots, fill strategy.md §2 via dialogue,
  then derive s2-domain-profiles / industry seeds. Run before wiki sync.
disable-model-invocation: true
---

# setup-domain-ops

Configure this repository for **your** Confluence + Jira tenant, then **derive domain cut lines from strategy** — not from any shipped industry template.

## When to run

- First clone of this open-source pack
- Adding a new product team / Confluence root
- Changing deliverable locale (`zh-CN` / `en`)
- Refreshing domain modules after strategy changes

## Agent checklist

### A. Credentials & teams

1. Ensure root `.env` exists (`cp .env.example .env`) and ask user for:
   - `ATLASSIAN_EMAIL` / `ATLASSIAN_API_TOKEN`
   - `ATLASSIAN_BASE_URL` and `CONFLUENCE_BASE_URL` (never leave placeholder in production)
2. If `domain-knowledge/jira/team-roots.json` still has `your-site.atlassian.net`, offer to start from `team-roots.example.json`.
3. For each team, collect and write into `team-roots.json`:
   - `root_id` (Confluence page id)
   - `confluence_overview` URL
   - `jira.board_id`, `jira.jql_base`, `jira.agile_team`
   - `deliver_by_proposition` map (slug → `[dir, filename]`) — may be filled after themes are known
   - optional `aliases` / `s2_profile: "default"` when using the root profile file
4. Set `defaults.deliverable_locale` (`zh-CN` or `en`).

### B. Fill `strategy.md` §2 (required)

5. Open [`domain-knowledge/strategy.md`](../../../domain-knowledge/strategy.md). Keep §1 methodology; **fill §2** with the user's answers:
   - org / product boundary
   - subjects & markets
   - 3–8 candidate domain modules (business names + one-line axis)
   - typical eligibility→branch→outcome questions
   - time cycles; strengthen/weaken lists; policy vs implementation
6. Point at [`strategy.example.md`](../../../domain-knowledge/strategy.example.md) only as **format** (fictional Acme Orders) — **do not** copy its slugs into production profiles.
7. Stop if §2 still says placeholder / to-fill in critical rows; do not invent a fake industry.

### C. Derive machine profiles (required; human confirm)

8. From filled §2, draft and write:
   - `domain-knowledge/s2-domain-profiles.json` — `checklist_themes`, `s1_facets`, `s2.primary_facet_to_slug`, `domain_cues`, team-appropriate `strong_cues` / `route_overrides`
   - `domain-knowledge/s2-propose-industry-seeds.json` — `module_seeds` with `teams: ["<team_key>"]` (keep generic `strategy_dimensions`)
   - `domain-knowledge/jira/teams/<team>.json` — classify `facets` aligned to the same slugs
9. **Pause and ask the user to confirm** slugs / axes / keywords before continuing.
10. After confirm, remind:
    ```text
    @generate-knowledge-from-wiki <their overview URL>
    ```
11. Remind: do **not** commit production `curated/` / `extracted/` / `materialized/` or `.env` to a public fork.

## Hard stops

- Empty `checklist_themes` in `s2-domain-profiles.json` → wiki recognize / sync classify must not pretend modules exist. Tell user to finish B→C first.
- Never reintroduce shipped demo modules (`checkout`, `compensation-cbp`, …) unless the user's strategy actually contains them.

## Out of scope

- Running full S1–S6 for them (hand off to `@generate-knowledge-from-wiki`)
- Parsing `strategy.md` with scripts (Agent derives JSON; scripts only read JSON)
