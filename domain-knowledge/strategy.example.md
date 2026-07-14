# strategy.example.md — fictional industry fill-in

> **Format only.** Do not copy these modules into your default `s2-domain-profiles.json`.  
> Real teams edit [`strategy.md`](strategy.md) §2, then have Cursor derive profiles.  
> Chinese locale: [`strategy.example.zh-CN.md`](strategy.example.zh-CN.md).

**Path B (Walkthrough) — light context only (~2 min):**

1. **§2.1** — one-line product boundary (optional)
2. **§2.3** — the module table

The Path B **aha** is [`docs/BENCHMARK.md`](../docs/BENCHMARK.md) (with vs without brief), not this whole file. Skip §2.2, §2.4–§2.7, and the **Derive hint** (those are for Path C / `@setup-domain-ops`).

The sample below fills §2 for a fictional B2B ordering portal **Acme Orders**.

---

## 2. Organization & industry context (sample filled)

### 2.1 Organization & boundaries

- **Organization / product line**: Acme Orders (North America ordering portal)
- **Authoritative Confluence root**: `team-roots.json` → team `orders`, root_id `200001`
- **Team key**: `orders`
- **One-line product boundary**: Buyer place/amend order and fulfillment-visible status are in-domain; internal WMS pick algorithms are out of domain.

### 2.2 Industry & subjects

- **Industry type**: B2B ordering and fulfillment visibility
- **Rules mainly apply to**: buyer purchasers, seller support, internal fulfillment coordinators
- **Market or regulatory context**: no specific financial regulation; contract price follows quote version
- **Do versions / policy years change rules?**: quote `quote_version` affects whether place-order is allowed

### 2.3 Rule-dense areas (candidate domain modules)

| Candidate theme (business name) | One-line axis | Typical keywords (optional) |
|---------------------------------|---------------|-----------------------------|
| Place / amend order | Who may submit/change an order under which quote version | order, cart, amend, quote |
| Fulfillment visibility | Which stages/ETA the buyer sees | fulfillment, ship, ETA, status |
| Identity & access | Whether purchaser roles can see price / place orders | role, permission, buyer, SSO |
| Notifications | Who is notified how on status change | email, webhook, notify |

Example derived slugs (**examples only**): `ordering`, `fulfillment-visibility`, `identity-access`, `notifications`.

### 2.4 Typical adjudication questions

1. After a quote expires, can the purchaser still press Place order, and what banner do they see?
2. On partial ship, does the buyer portal show “In progress” or split status by line?
3. Can a read-only observer role see contract price?

### 2.5 Time & cycles

- Quote validity, promised ship window, cancel cutoff (per contract terms pages)

### 2.6 Strengthen / weaken

| Strengthen | Weaken |
|------------|--------|
| Quote version, place-order eligibility, portal-visible status | WMS pick paths, internal Slack on-call tables |

### 2.7 Policy vs implementation

- **Normative layer**: commercial terms / quote policy Confluence pages
- **Implementation layer**: Orders API field tables → provenance, not rule mainline

---

## Derive hint (for the agent — skip on Path B)

From the table above, generate four `checklist_themes`, `facet-ordering` (and related) `s1_facets`, and `s2.domain_cues`; set `module_seeds` `teams` to `["orders"]`. Human-confirm before wiki sync.
