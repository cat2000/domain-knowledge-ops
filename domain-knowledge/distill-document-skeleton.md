# Recommended `curated` section skeleton (domain-first)

For **`generate-knowledge-from-wiki/RUNBOOK.md` S4/S5 (work draft)**. **S6** produces the source-language brief; **S7** converts to the target locale. Align with [`distill-quality-bar.md`](distill-quality-bar.md), [`distill-authoring-contract.md`](distill-authoring-contract.md), and [`strategy.md`](strategy.md).  
Scripts **do not author semantics** — they only **validate** (see `scripts/distill/domain_layout.py`).

Chinese locale: [`distill-document-skeleton.zh-CN.md`](distill-document-skeleton.zh-CN.md).  
Deliverable label map (en ↔ zh-CN): [`language/deliverable-locale-tokens.json`](language/deliverable-locale-tokens.json).  
Agents emit labels for `defaults.deliverable_locale` from that map; this English doc cites **English** labels only.

> Heading tokens below use **English deliverable labels**. For `deliverable_locale=zh-CN`, agents look up the zh-CN equivalents in `language/deliverable-locale-tokens.json`.

---

## When to use this skeleton

- Mixed themes: membership/advisor-visible outcomes **and** path/field/gateway maps (checkout, rewards, push, etc.).
- Pure policy pages may use only Overview + business rules + Provenance (skip "implementation support").
- Clear non-business **Pass** (S2) does not use the full skeleton — use the RUNBOOK Pass stub only.

---

## Recommended order (top → bottom)

1. **Title**: domain object visible at a glance (avoid API-only titles).
2. **`## Doc purpose & readers`** or **`## Overview & scope`**: who reads this and which **business** problem (1–2 paragraphs).
3. **`## Domain overview`** (optional): one sentence of industry meaning.
4. **`## Input disposition summary`** (**S5 required**): disposition of `contract_candidate` / `evidence_note` / `noise_context`, high-value evidence promotion, semantic & source-order normalization.
5. **`## Domain model`** (**S5 required**): layered First-class business objects, Metrics/fields, Display containers, Object relationships, State machines/state transitions, Boundary candidates.
6. **`## Ordering rationale`** (**S5 required**): `Chain N: title — why this order`; heading text not bold, not code.
7. **`## Closed-loop decision chains`** (**S5 required**): each chain states Domain object / State change / Business action / Display containers/field anchors.
8. **`## Pending-decision critical issues`** (**S5 required**): each item states `Linked chain` or `Linked prerequisite domain`, plus `Decision impact`.
9. **`## Structured detail handoff`** (**S5 conditional**): maps, enums, field lists, formulas/thresholds, windows, visible copy — tables or layered lists.
10. **`## Implementation & data support`** or **`## Data & interface / presentation notes`** (as needed): paths, JSON fields, gateway maps here — never let paths and backtick fields dominate the first half of the doc.
11. **`## Provenance`**: Confluence (and org-approved policy links) only.

---

## Reader layers

Default S5 serves three readers, in this order:

- **Decision readers (biz/product/ops)**: scope, key thresholds, windows, main outcomes, open conflicts (L1).
- **Execution readers (requirements/QA/delivery)**: full rule chains for acceptance (L2).
- **Implementation readers (eng/data)**: APIs/fields/maps last — never front-loaded (L3).

Quick self-check before save:

- Can each rule be stated as **who + when + trigger + visible result**?
- Does every S5 chain mount on a first-class domain object, with fields/APIs/pages demoted to anchors/containers?
- Is every structured-detail subsection a table or layered list (not a prose mush)?
- Can a non-technical reader grasp the main rules in 3–5 minutes?
- Are implementation details under support/provenance, not crowding the core-rules section?

---

## Anti-patterns (scripts may flag)

- First half dominated by `/rest/`, `` `Gateway` ``, or mirrored Confluence heading dumps (`### [title](url)`).
- No independent business-rules narrative — only an API inventory.

---

## Relation to validators

```bash
python3 scripts/distill/domain_layout.py --root-id <rootPageId>
```

Failure exits **1** (or `--warn-only`); suitable for CI with other page gates.
