---
name: setup-domain-ops
description: >-
  One-time setup: credentials, company/business intro → industry module
  template (confirm), Confluence space URL(s), Jira board id(s). Derives
  strategy §2 draft and profiles before wiki sync. See docs/TEAM_ROOTS_V3.md.
disable-model-invocation: true
---

# setup-domain-ops

Configure this repo for **your** tenant with a **short** dialogue.  
Target model ([`docs/TEAM_ROOTS_V3.md`](../../../docs/TEAM_ROOTS_V3.md)): **one Confluence space = one library**; each Jira team mounts `libraries[]`. Until v3 JSON is wired, still write today’s `team-roots.json` shape (one team record can hold overview + board); keep the **same slim questions**.

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
3. If `team-roots.json` still has `your-site.atlassian.net`, offer to copy from `team-roots.example.json`.

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

### D. Confluence spaces (libraries)

10. For each space, collect **overview URL** (or homepage id). One space → one library / one `root_id` subtree.
11. Write into `team-roots.json` (v2 today: on the team or shared root fields; v3 later: `libraries.*`).
12. Remind next step per space:
    ```text
    @generate-knowledge-from-wiki <overview-URL>
    ```

### E. Jira boards (teams)

13. For each delivery team, collect **board_id** (+ optional display name / agile team / jql_base).
14. Record which **libraries** this board uses (default: libraries just configured).
15. Write `jira.board_id` (and related) into `team-roots.json`; remind:
    ```text
    @add-knowledge-from-jira team=<team_key>
    ```

### F. Hygiene

16. Remind: do **not** commit production `curated/` / `extracted/` / `materialized/` or `.env` to a public fork.

## Hard stops

- Empty company/intro and empty module table → stop; do not invent an industry.
- Empty `checklist_themes` → do not pretend Recognize/wiki modules exist.
- Never reintroduce shipped demo modules (`checkout`, `compensation-cbp`, …) unless the user’s confirmed strategy contains them.
- Do not scrape the public web into brief rule bodies; optional public hints for *module naming* only, always confirmed.

## Out of scope

- Running full S1–S7 (hand off to `@generate-knowledge-from-wiki`)
- Parsing `strategy.md` with scripts (agent derives JSON; scripts read JSON only)
- Multi-space merge into one `_deliver/` (deferred; see TEAM_ROOTS_V3)
