# Domain knowledge · goals, context, and method

Human-readable ruler for this repo’s **team domain knowledge**: why it exists, how good is “good enough,” and how to cut modules.

**Open-source default**: §1 methodology is filled; **§2 industry context must be filled by you** (via Cursor, prefer `@setup-domain-ops`). Module cuts do **not** come from any shipped industry table.

Machine configs (`s2-domain-profiles.json`, `s2-propose-industry-seeds.json`) are **derived by Cursor from a filled §2**, then human-confirmed before S1/S2. Scripts **do not** parse this file’s prose.

Fill example (fictional; not default modules): [`strategy.example.md`](strategy.example.md).  
Chinese locale: [`strategy.zh-CN.md`](strategy.zh-CN.md).  
Deliverable label map (en ↔ zh-CN): [`language/deliverable-locale-tokens.json`](language/deliverable-locale-tokens.json).  
Agents emit labels for `defaults.deliverable_locale` from that map; this English doc cites **English** labels only.

---

## 1. Purpose

Turn Confluence domain pages into a **reusable team domain library** for delivery and product discovery:

1. **Onboarding** — shorten time-to-effective contribution.
2. **Story context** — spot ambiguity, boundaries, and risk **before** sprint churn.
3. **Discussion fuel** — connect known rules to possible new value.

### Orientation: business domain knowledge (clear rules, thorough extraction)

- **Business first**: prioritize rules, flows, eligibility, constraints, and user/business-visible outcomes; demote collaboration schedules, ticket matrices, pure ops to provenance or soft notes.
- **Clear rules**: conditions, exceptions, branches, frequencies, windows in scannable sentences; align terms with [`language/glossary.md`](language/glossary.md).
- **Thorough extraction**: exhaust business-relevant material under `materialized/` — anything that affects “should this happen / will there be a visible consequence” must be checkable in `curated/`; **not** a dump of engineering noise.

### Audiences and density

1. **Business / product / ops (decision readers)** — ship? compliant? conflicting policy?
2. **Requirements / QA / delivery (execution readers)** — stories, acceptance, gap lists.
3. **Engineering / data (implementation readers)** — how fields/APIs map to business meaning — never dominate the brief.

Density layers:

- **L1 (~30s)**: scope, subjects, key thresholds/windows, main outcomes, open conflicts.
- **L2 (~3–5 min)**: full rule chains (condition–branch–exception–outcome), acceptance-ready.
- **L3 (on demand)**: APIs, fields, tickets, history — provenance only.

Constraint: S5 body at least L1+L2; each rule should answer “who sees what result under which condition”; expand abbreviations on first use.

### Knowledge emphasis

| Strengthen | Weaken |
|------------|--------|
| Shared language, business rules & exceptions | Generic engineering norms, unrelated toolchains |
| **Business meaning** of flows and states | Field dumps with no business semantics |
| Risk & ambiguity (business lens) | Pure ops / deploy detail |
| User/business-visible commitments | Sprint/retro, bug lists, collaboration cadence itself |

### Briefs must hold full business rules (not an index library)

**S2–S3** only recognize and aggregate; **S4–S5** work drafts and **S6/S7** briefs carry full rule text. **Do not** replace rule chains with “see `materialized/`”.

### Compose priority (S4–S5)

Aligned with [`distill-quality-bar.md`](distill-quality-bar.md):

1. **Semantic remount** — organize prose by domain propositions.
2. **Truth over noise** — demote collaboration/engineering noise; keep Confluence provenance.
3. **Completeness (business side)** — write and verify every clause that affects visible outcomes.
4. **Language** — **no translation in S1–S6**; target reader language only in **S7** (below).

### Merge rules

- One rule = one adjudication question.
- Merge by business trigger, not page title.
- Same word → same meaning; conflicts are never silent overrides.
- Mainline first, support later (implementation detail → provenance).

### S5 mandatory field template (machine gates)

Each `###` rule cluster must include: `rule gist`, `applicable subject`, `conditions`, `handling branches`, `time windows`, `exceptions`, `user-visible effect`, `reference sources`. Locale labels vary; agents look up zh-CN equivalents in `language/deliverable-locale-tokens.json`.

### Layout: prefer lists over wide tables

Default to headings + lists + short paragraphs; short tables only for strong alignment. Layout serves content.

### Core capability: Cursor extracts, organizes, and adjudicates

Scripts sync drafts; **brief judgment** is the Cursor agent. Scripts **do not** call cloud LLMs to write `curated/`. Process: [`generate-knowledge-from-wiki/RUNBOOK.md`](../.cursor/skills/generate-knowledge-from-wiki/RUNBOOK.md).

### Language: S6 source brief · S7 locale brief

| Stage | Path | Language |
|-------|------|----------|
| Sync | `extracted/`, `materialized/` | Confluence source |
| Recognize + aggregate | `_aggregate/`, closure, checklist | no translation |
| Work draft | `_deliver/…-work-draft.md` | matches source |
| Source brief | `_deliver/…-source-brief.md` (**S6**) | matches source (adjudicated; no translation) |
| Locale brief | `_deliver/…-domain-brief.md` (**S7**) | `deliverable_locale` (often zh-CN / en) |

---

## 2. Organization & industry context (**fill in**)

> This section is the **industry ruler**. Do **not** run Recognize (S2) or rely on `s2-domain-profiles.json` module tables until it is filled — open source ships an empty shell.

Use `@setup-domain-ops` or Cursor dialogue to replace placeholders with your real context.

### 2.1 Organization & boundaries

- **Organization / product line**: (to fill)
- **Authoritative Confluence root**: see [`jira/team-roots.json`](jira/team-roots.json) → `libraries.<key>.root_id` / `confluence_overview` (team mounts that library via `teams.<key>.libraries`)
- **Team key**: (must match a key under `teams` in `team-roots.json`, e.g. `demo`)
- **One-line product boundary**: (to fill — what is in-domain vs explicitly out)

### 2.2 Industry & subjects

- **Industry type**: (to fill — e.g. B2B ordering, content platform, internal tool, financial compliance…)
- **Rules mainly apply to**: (to fill — roles / customer types / channels)
- **Market or regulatory context**: (to fill; or “no specific regulation”)
- **Do versions / policy years change rules?**: (to fill)

### 2.3 Rule-dense areas (candidate domain modules)

List **3–8** blocks worth their own briefs (business names; slugs suggested later by the agent):

| Candidate theme (business name) | One-line axis (what is decided) | Typical source keywords (optional) |
|---------------------------------|----------------------------------|--------------------------------------|
| (to fill) | (to fill) | (to fill) |
| (to fill) | (to fill) | (to fill) |
| (to fill) | (to fill) | (to fill) |

### 2.4 Typical adjudication questions (eligibility → branch → outcome)

Write at least 3 questions you argue about most often, in business language:

1. (to fill) e.g. “Who enters which state under which condition, and what does the user see?”
2. (to fill)
3. (to fill)

### 2.5 Time & cycles

- **Key windows / settlement cycles / enrollment windows**: (to fill; or “no shared cycle”)

### 2.6 Strengthen / weaken (for this industry)

| Strengthen (mainline prose) | Weaken (provenance or one line) |
|-----------------------------|----------------------------------|
| (to fill) | (to fill) |

### 2.7 Policy vs implementation

- **Where normative policy / business truth lives**: (to fill)
- **How implementation (API/fields/SQL) is demoted**: (to fill — default: “implementation notes / provenance”)

---

## 2-annex · From strategy to profiles

1. **Fill §2** (human + Cursor).
2. Cursor drafts from §2:
   - [`s2-domain-profiles.json`](s2-domain-profiles.json) → `checklist_themes`, `s1_facets`, `s2.primary_facet_to_slug`, `domain_cues`, …
   - [`s2-propose-industry-seeds.json`](s2-propose-industry-seeds.json) → `module_seeds` (optional `teams: ["<key>"]`)
   - Optional: [`jira/teams/<key>.json`](jira/teams/demo.json) classify facets
3. **Human confirm** slugs / axes / keywords, then write files.
4. Run `@generate-knowledge-from-wiki` (S1 → S2…).

If `checklist_themes` is still empty, Recognize scripts and the wiki skill **hard-stop** and point back here.

---

## 3. Modeling references (optional)

| Reference | Use |
|-----------|-----|
| Domain-Driven Design | Bounded contexts, ubiquitous language → glossary & theme rules |
| Analysis Patterns | Recurring structures as sections |
| DSL thinking | Controlled vocabulary + bullets in rule-dense areas |

The pipeline syncs and aggregates; these methods guide how Cursor cuts and names drafts.

---

## 4. Multi-team / multi-product

- Each authoritative root → `extracted|materialized|curated/by-root/<root_id>/`
- Team metadata: [`jira/team-roots.json`](jira/team-roots.json) (any N keys)
- Entry: `@generate-knowledge-from-wiki` + Confluence URL → prep → human sets module **Status** to **`confirmed`** → Compose

**S1 facet classification** only reads `s2-domain-profiles.json` (derived from this section), **not** a built-in industry pack. Misses → `facet-unmatched/`.

---

## 5. Subtree roots vs parent roots

| Approach | Scope | Directory |
|----------|-------|-----------|
| Pass a child page as root | That page and descendants | `by-root/<childId>/` |
| Pass a parent page as root | Parent and all descendants | `by-root/<parentId>/` |

Practice: each product line picks **one authoritative parent root** as the full library entry; child roots suit increments, not replacements.

---

## 6. Implementation checklist

| Consensus | Current implementation |
|-----------|------------------------|
| Any Confluence page as root | `sync_domain_knowledge_from_confluence.py` → `by-root/<rootPageId>/` |
| Business domain first | RUNBOOK S4–S5 + `distill-quality-bar.md` |
| Industry cuts from strategy | Fill §2 → derive profiles; empty shell → hard stop |
| Reader-facing brief | `_deliver/…-domain-brief.md` (**S7**; after S6 `…-source-brief.md`) |

---

## 7. When drafts feel “messy” (general)

Common causes: source pages are implementation notes; extract keeps raw text and broken tables; mixed quality under one tree.

Relief: when Cursor drafts, **write business rules fully and demote technical noise**; on Confluence, separate policy pages from integration pages; for existing drafts, targeted “rewrite per strategy” is fine.

---

## 8. First principles: distill quality

**High-quality business rules = complete, unambiguous statements of adjudicable propositions** — that needs semantic judgment. Scripts can improve input shape and run deterministic checks; they cannot replace Cursor + humans.

Scripts may: companion inventories, closure coverage, heuristic quality reports. Scripts must not pretend “stronger regex = domain truth.”

---

## 9. Definitions of done (three levels)

| Friendly name | Meaning |
|---------------|---------|
| **Closed** | Pages under `materialized/` that participate in acceptance have a landing in `_materialization_closure.json` (or equivalent) |
| **Brief (path-level)** | A single-topic **S7** locale brief is traceable (and a matching **S6** source brief exists) |
| **Core themes briefed** | Checklist **`confirmed`** rows have completed S6→S7 |

Checklist status **`confirmed`** = module cuts accepted and Compose authorized. Externally commit only **S7** locale briefs (`*-domain-brief.md`); upstream must include **S6** `*-source-brief.md`.

Display: [`TEAM_KNOWLEDGE_BASE.md`](../TEAM_KNOWLEDGE_BASE.md). Coverage: `scripts/distill/coverage.py`.

---

## Relation to README

- [`README.md`](README.md): directory map.
- [`TEAM_KNOWLEDGE_BASE.md`](../TEAM_KNOWLEDGE_BASE.md): reading entry.
- **This file**: strategy & method; **§2** is your industry SSOT (human); machine profiles derive from it.
