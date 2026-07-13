# Jira pipeline · root cause and redesign

Chinese locale: [`pipeline-design.zh-CN.md`](./pipeline-design.zh-CN.md).

Why the old Jira script chain produced **“many tickets, little domain knowledge”**, and how the pipeline must align with **unified Compose** knowledge density (S6 source brief → S7 locale brief).

**Current stage names**: Ingest → Classify → Recognize (shared) → Compose (shared **S3→S7**). Legacy Extract / Integrate are deleted — no audit/compat entry. See [`.cursor/skills/add-knowledge-from-jira/RUNBOOK.md`](../../.cursor/skills/add-knowledge-from-jira/RUNBOOK.md).

---

## 1. Root causes

### 1.1 Wrong objective: coverage ≠ knowledge density

| Was optimized | Should optimize |
|---------------|-----------------|
| Every ticket has `raw` + `attribution` | Confirmed themes contain **adjudicable business rule text** |
| `check_jira_pipeline` only checks files exist | Check Jira evidence enters S3/S4/S5 via S2 closure |
| Report “Classify/Extract/Integrate done” with no substance | Report “Jira detail entered unified S3–S5 and is checkable” |

**Essence**: the Jira path was treated as a **data / appendix pipe**, not a first-class evidence source for the domain library.

### 1.2 Missing product layers: map without body

Wiki Compose has clear layers:

```text
materialized/ (source) → _aggregate/<slug>/ (S3) → _deliver/…-work-draft.md (S4/S5)
  → …-source-brief.md (S6) → …-domain-brief.md (S7; zh-CN locale uses locale-brief suffix)
```

The old Jira path collapsed to:

```text
raw/ → by-theme/requirement-summary.md (Epic-cluster bullets)
  → end-of-brief “Jira supplement (to verify)”
```

A parallel “Jira excerpt” layer was attempted at brief parity — **Classify defaults to an index**, while Integrate **appendices pretended to be merges**. The fix is not thicker appendices; admit Jira business evidence at the **S3 input layer** of unified Compose.

### 1.3 `business_extract` was too wide

Scripts once set `business_extract: true` for “theme hit + has comments”, which:

- Pulled large Extract filters full of platform duplicates, Verified-only, no-AC tickets;
- Inflated expectations of “600+ business tickets” while **rule-rich** text was closer to ~40% rich per theme.

**Essence**: **intake queue** (might contain rules) was not separated from **distill queue** (must read full text to write rules).

### 1.4 Asymmetry vs Confluence

| Confluence (Compose) | Jira (legacy) |
|----------------------|---------------|
| S4/S5 write full rule chains (source language) | Cluster summaries + few KEYs |
| Confirmed → S4–S7 | Confirmed triggered only try-appendices |
| `strategy` eligibility–branch–outcome template | Ticket AC not forced into that template |

### 1.5 Channel vs proposition (fixed; Extract lagged)

Mall/Hui must not become checklist rows, but Jira tickets **must** carry `product_line` in attribution so channel-specific rules stay findable.

### 1.6 `gateway` / `requirements` are not “unfinished confirmed”

They are **attribution sinks** (mapping engineering, collab noise), **not** peer propositions. **Forbidden** to Extract them or promote them to checklist **confirmed** for coverage. CNGW tickets with member-visible rules should set **`primary` on checkout / contests / …**; pure API/Session tickets stay `engineering` + `gateway` (index only).

---

## 2. Redesign principles

1. **Separate tracks**: `attribution` = Classify triage; `distill_tier` / `proposition_extract` = S3 admission; **rule writing** is Agent work in S4/S5 from business causality.  
2. **Three product layers** (mandatory for confirmed themes):

| Layer | Files | Owner | Content |
|-------|-------|-------|---------|
| **Index** | full KEY index, gap-scan | `read_business.py` | Coverage, clusters, rich-ticket lists |
| **Evidence** | `raw/` + `materialized/` + `attribution/` | Ingest/Classify | Source of truth, readable copy, S3 admission |
| **Merge** | `_aggregate/`, work drafts, S6/S7 briefs | Unified Compose | Rule chains with Confluence |

3. **Gates**: `domain_check jira --full-raw` for prep; `domain_check distill` for Compose after **S7**.  
4. **Forbidden** to report “done” via ticket counts or legacy Extract/Integrate; judge by Jira detail fidelity inside `_aggregate/` / drafts / briefs.

---

## 3. Script ↔ skill map

| Stage | Scripts |
|-------|---------|
| Ingest | `run_jira_ingest.py` · `fetch.py` · `materialize.py` |
| Classify | `attribute.py` · `read_business.py` |
| Unified S3 input | `distill/proposition_extract.py` |

See [`README.md`](README.md) and [`.cursor/skills/add-knowledge-from-jira/SKILL.md`](../../.cursor/skills/add-knowledge-from-jira/SKILL.md).

---

## 4. Necessity first (coverage-rate trap)

**Wrong metric**: `KEYs cited in prose / distill_queue size` → drives appendix bloat and platform-duplicate tickets.

**Right question**: for each **adjudicable proposition** visible to users/advisors, did we absorb **Confluence macro rules** and **Jira detail decisions (AC / comment last-wins)**?

| Layer | Source | Answers |
|-------|--------|---------|
| **Policy rules** | Confluence `_deliver` | Eligibility, cycles, thresholds, state machines |
| **Business detail** | Jira `raw/materialized` + attribution | Fields, copy, display conditions, AC/comment decisions |
| **Index** | Gap-scan | Whether a platform ticket exists for traceability |

**Typical distill_queue split (illustrative)**

| Category | Share (example) | Must enter rule body? |
|----------|-----------------|------------------------|
| Platform variants (iOS/Android/… same rule) | majority | **No** — one proposition + representative KEYs |
| Gateway / field mapping | some | **No** — engineering track; merge only if **user-visible** |
| Off-theme reports / tracking | few | **No** — index or other domain |
| **Core propositions** | minority | **Yes** — write by **proposition cluster**, not ticket pile |

A modest ticket-level citation rate can be fine if **~10–15 proposition clusters** are clear and Wiki-aligned. Fix **cluster merge narrative**, not more platform copies.

**Operating rules**

1. **Ticket = evidence, not knowledge unit** — unit = one eligibility–branch–outcome proposition.  
2. **Last-wins in comments** — excerpts must prefer later sprint/comment decisions.  
3. **No duplicate domains** — notifications/contest cards in another queue **reference** that domain; do not paste full text.  
4. **Triage before distill** — split `distill_queue` into `proposition_core` / `platform_variant` / `index_only`.

**Improvement direction (not coverage farming)**

- `proposition_extract.py`: read Confluence closure for confirmed slugs **and** Jira business evidence from attribution.  
- Report with Jira source pages in `_aggregate/`, S5 absorption, S7 fidelity — not ticket ratios.  
- Cursor Compose: merge Confluence + Jira condition–branch–outcome in S4/S5; no post-S7 appendix.
