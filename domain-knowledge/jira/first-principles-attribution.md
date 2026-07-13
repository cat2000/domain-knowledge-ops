# Jira attribution · first principles (aligned with Confluence)

Chinese locale: [`first-principles-attribution.zh-CN.md`](./first-principles-attribution.zh-CN.md).

## The real question

Ticket attribution must answer: **which business-proposition knowledge chain should this evidence enter** (same as `DOMAIN_MODULE_CHECKLIST` / `_deliver`), **not** which app implements it.

| Dimension | Question answered | Field | New domain? |
|-----------|-------------------|-------|-------------|
| **Business proposition `primary` / `themes[]`** | Which rule family (checkout, rewards, contests, …) | `primary`, `themes` | **Yes** (only checklist slugs) |
| **Channel `product_line`** | Mall App / Reporting App / Gateway side | `product_line` | **No** (label only; no `_deliver/`) |
| **Material kind `material_kind`** | Normative business / mapping engineering / collaboration noise | `material_kind` | **No** (drives `signal`) |

Aligned with [`strategy.md`](../strategy.md): one Confluence space is typically one bounded context; product-line parent pages are **subtree roots**, not peer domain folders next to checkout / CBP.

## `gateway` / `requirements` are not domains

Checklist rows **`gateway`** and **`requirements`** are **Jira attribution sinks** + Confluence engineering/collab buckets — **not** peer business propositions:

| slug | Meaning | Why no `_deliver/` brief |
|------|---------|---------------------------|
| **`gateway`** | CNGW / API mapping / Session / Consent **implementation** work | Dev vocabulary; member-visible rules belong on business slugs |
| **`requirements`** | Grooming, test engineering, retro, unmatched **collaboration noise** | Not policy / eligibility / outcome chains; `signal: pass` or thin engineering |

**Practice**

- `primary: gateway|requirements` is a **triage result**. If the ticket has **normative AC**, scripts/Cursor should move **`primary` to a business slug** (or dual-mount via `themes[]`) — never promote the sink bucket to **confirmed**.
- Jira business evidence enters unified Compose only through **confirmed** themes; `gateway` / `requirements` are **not** coverage gaps (same class as non-domain / `facet-unmatched`).
- Confluence `facet-gateway/` may keep **technical design** material — separate track from Compose locale briefs.

## Team config (proposition lexicon · Epic · title)

| Team | Config |
|------|--------|
| Demo (shipped) | [`teams/demo.json`](teams/demo.json) |
| Your teams | `teams/<team>.json` keyed from [`team-roots.json`](team-roots.json) |

`attribute.py` loads via `jira_team_attribution.py`: team **`facets`** replace global keyword bags; **`epic_primary` / `title_primary`** beat keywords; **confirmed checklist slugs** → `normative_business` + `distill_queue`.

## Decision order (scripts + Cursor)

1. **Collaboration noise** → `material_kind: collaboration_noise`, `signal: pass`, `primary: requirements` (or `gateway` for pure CNGW ops).
2. **Engineering/mapping with no user-visible business effect** → `material_kind: mapping_engineering`, `signal: engineering`, `primary: gateway` or `requirements` (**sink, not a proposition**).
3. **Business proposition** → Epic/title rules (`teams/*.json`) → team facet keywords; `themes[]` may cross domains; do not leave `primary` on a sink when the body clearly belongs to a confirmed slug (Cursor corrects).
4. **`product_line`** → detect `[Mall]` / `[Hui]` / `CNGW` / `Gateway` etc. **without** changing `primary` selection.
5. **Parent inheritance** → when child proposition is unclear, use `raw.parent` summary; child AC/comments may override.

## Recognize · shared confirmation page

- **Do not** add `mall-app` / `hui-app` checklist rows just because many tickets carry `[Mall]` / `[Hui]`.
- Add an incremental theme only when a **new orthogonal policy/eligibility/outcome chain** appears (and roughly ≥5 Stories with no Wiki theme).
- Existing rows: optional notes for Jira samples / `product_line` mix.

## Distill queue `distill_queue` (and `business_extract`)

| Field | Meaning |
|-------|---------|
| `substance_chars` / `substance_tier` | Description+comments size; empty/thin/medium/rich |
| `distill_queue` | Theme index queue |
| `distill_tier` / `proposition_extract` | See [`pipeline-design.md`](pipeline-design.md) §4; S3 admits only `proposition_core` / `platform_variant` |
| `business_extract` | Aligned with `distill_queue` (D-index) |

**Enter `distill_queue`** (`jira_substance.py`): `material_kind: normative_business` and (medium/rich body, or thin+rule-like text, or Bug/Defect with a conclusion).  
**Do not enter**: Verified-only comments, Spike without AC, collaboration noise, thin engineering tickets.

## Script split (no LLM)

| Script | Role |
|--------|------|
| `scripts/jira/lib/jira_substance.py` | Body size, `distill_queue` |
| `scripts/jira/lib/jira_first_principles.py` | Single-ticket attribution |
| `scripts/jira/steps/attribute.py` | `attribution/*.yaml`, `_ticket_attribution.json` |
| `scripts/jira/lib/jira_proposition.py` | `distill_tier`, `proposition_id`, core proposition table |
| `scripts/distill/proposition_extract.py` | S3: admit authorized Jira business evidence into unified candidates |
| `scripts/jira/steps/read_business.py` | Classify indexes: full KEY index, gap-scan |
| `scripts/jira/steps/check_pipeline.py` | `--full-raw` prep integrity |

**Cursor**: semantic merge in unified Compose (**S3→S7**); see [`pipeline-design.md`](pipeline-design.md).
