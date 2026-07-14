---
name: setup-domain-ops
description: >-
  One-time setup: credentials, company/business intro → industry module
  template (confirm), Confluence space URL(s), Jira board id(s). Writes
  team-roots.json as v3 (libraries + teams mounting them). See docs/TEAM_ROOTS_V3.md.
disable-model-invocation: true
---

# setup-domain-ops

Configure this repo for **your** tenant with a **short** dialogue.  
Model ([`docs/TEAM_ROOTS_V3.md`](../../../docs/TEAM_ROOTS_V3.md)): **one Confluence space = one library**; each Jira team mounts `libraries[]`.

**Path C default (single library):** one space + one board → one `libraries.*` entry + one `teams.*` with `libraries: [<that key>]`.  
Write **`version: 3`** JSON. Do **not** write the old v2 shape (root/overview on the team). Template: [`team-roots.example.json`](../../../domain-knowledge/jira/team-roots.example.json). Multi-mount illustration only: [`team-roots.v3.example.json`](../../../domain-knowledge/jira/team-roots.v3.example.json).

## When to run

- First clone of this pack
- Adding a Confluence space (library) or Jira board (team)
- Changing deliverable locale (`zh-CN` / `en`)
- Refreshing module cuts after strategy changes

## Agent checklist

### A. Credentials

1. Ensure root `.env` exists (`cp .env.example .env`) and collect:
   - `ATLASSIAN_EMAIL` / `ATLASSIAN_API_TOKEN`
   - `ATLASSIAN_BASE_URL` and `CONFLUENCE_BASE_URL` (no placeholders in production)
2. Set `defaults.deliverable_locale` (`zh-CN` or `en`) when editing `team-roots.json`.
3. If `team-roots.json` still has `your-site.atlassian.net`, offer to copy from `team-roots.example.json`, then replace placeholders.

### B. Company intro → industry template (required)

4. Ask only:
   - **Company / product name**
   - **Short business intro** (industry, who rules apply to, one-line in-domain vs out-of-domain)
5. As an **industry expert**, draft a **best-practice domain cut** (not product rule text):
   - 3–8 candidate modules (business name + one-line axis)
   - Light `strategy.md` §2 fill from that draft (subjects, strengthen/weaken, a few adjudication questions)
6. Use [`strategy.example.md`](../../../domain-knowledge/strategy.example.md) only as **format**. Do **not** copy Acme / demo slugs into production profiles.
7. **Pause for human confirm** on the module table (edit/rename/drop rows). Do not invent a fake industry if the intro is empty — ask again.

**Template vs truth:** the draft is a **cut template**. Adjudicated rules in briefs come later from Confluence + Jira — never treat the template as SSOT.

### C. Derive machine profiles (after confirm)

8. From confirmed modules + §2 draft, write:
   - `domain-knowledge/s2-domain-profiles.json` — themes, facets, cues
   - `domain-knowledge/s2-propose-industry-seeds.json` — `module_seeds` (team keys as known)
   - `domain-knowledge/jira/teams/<team>.json` — classify facets aligned to slugs (when team exists)
9. Do not continue to wiki with empty `checklist_themes`.

### D. Confluence spaces → `libraries.*` (v3)

10. For each space, collect **overview URL** (or homepage id). One space → one library key (stable slug, e.g. product or space_key lowercased).
11. Write under `libraries.<library_key>`:
    - `display_name`, `root_id` / `library_id` (homepage id), `confluence_overview`, optional `space_key`, `s2_profile`
    - `deliver_by_proposition` from confirmed modules, using the **active** `defaults.deliverable_locale` S7 filename:
      - `en` → `"<slug>": ["<slug>", "<slug>-domain-brief.md"]`
      - `zh-CN` → `"<slug>": ["<slug>", "<slug>-领域知识定稿.md"]`
      - (suffix from `domain-knowledge/language/deliverable-locale-tokens.json` → `filenames.locale_brief_suffix`)
      Do **not** hard-code English `*-domain-brief.md` when locale is `zh-CN`.
12. Set `defaults.default_library` to the primary (usually the only) library key.
13. Remind next step per space:
    ```text
    @generate-knowledge-from-wiki <overview-URL>
    ```

### E. Jira boards → `teams.*` mounts (v3)

14. For each delivery team, collect **board_id** (+ optional display name / agile team / jql_base).
15. Write under `teams.<team_key>`:
    - `libraries: ["<library_key>", …]` — Path C single-lib: one entry (the library from D)
    - `jira.board_id` and related fields; `attribution_config` when present
    - **Do not** put `root_id` / `confluence_overview` / `deliver_by_proposition` on the team (those live on the library)
16. Set `defaults.default_team` when there is a primary team. Remind:
    ```text
    @add-knowledge-from-jira team=<team_key>
    ```

### F. File shape checklist (before finish)

17. `team-roots.json` must have `"version": 3`, non-empty `libraries`, and every team with non-empty `libraries[]`.
18. Single-library Path C is done when: one library + one team mounting it + profiles non-empty + handoff commands shown.
19. Remind: do **not** commit production `curated/` / `extracted/` / `materialized/` or `.env` to a public fork.

## Hard stops

- Empty company/intro and empty module table → stop; do not invent an industry.
- Empty `checklist_themes` → do not pretend Recognize/wiki modules exist.
- Never reintroduce shipped demo modules (`checkout`, `compensation-cbp`, …) unless the user’s confirmed strategy contains them.
- Do not scrape the public web into brief rule bodies; optional public hints for *module naming* only, always confirmed.
- Do not write v2-only team records (overview + board on the same object without `libraries{}`).

## Out of scope

- Running full S1–S7 (hand off to `@generate-knowledge-from-wiki`)
- Parsing `strategy.md` with scripts (agent derives JSON; scripts read JSON only)
- Multi-space merge into one `_deliver/` (deferred; see TEAM_ROOTS_V3)
- Full multi-mount classify/risk (config may list several libraries; runtime still uses primary mount until a later slice)
