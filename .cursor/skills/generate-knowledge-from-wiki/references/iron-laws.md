# generate-knowledge-from-wiki · iron laws (load on demand)

> Agent: read this for **Compose / disputes**. Day-to-day prep uses `SKILL.md` + `RUNBOOK.md`.  
> Chinese locale: [`iron-laws.zh-CN.md`](./iron-laws.zh-CN.md).

**confirm** = approve module cuts · **source brief** = S6 (source language) · **locale brief** / **brief** = S7 (target locale) · **continue** = resume Compose. (zh-CN strings for these tokens: `deliverable-locale-tokens.json`.)

## Iron laws

0. **Strategy-first hard stop**: empty `checklist_themes` or placeholder-heavy `strategy.md` §2 → stop; `@setup-domain-ops`. Never invent shipped industry modules.
1. Default **prep**: Ingest + Recognize (S1→S2) → **pause** on checklist; **no translation in S1–S6**.
2. **Compose** after **confirm** + **continue**: S3→S4→S5→**S6→S7** for **confirm** rows only.
3. S3 = fidelity routing/index/transfer; S4 = domain model; S5 = work draft in source language; **S6** = source-language reader productization (**no new semantics, no translation**); **S7** = locale conversion of S6 only (`deliverable_locale`; **expression only**).
4. **confirm** ≠ briefs already exist (need S6 + S7 when locale differs or when the canonical locale filename is required).
5. S1 `facet-*` = machine bucketing ≠ confirmed checklist slug (proposition recognize is S2).
6. Source of truth is Confluence; do not treat hand-edited `materialized/` as authority.
7. **S1 integrity**: page errors block S2 unless explicit `--allow-partial` (carry gap risk forward).
8. **S1 materialization manifest**: `materialized/` matches current source set; purge stale `.md` each run.
9. Compose outputs live under `curated/by-root/<R>/` (`_deliver/`, `_aggregate/`).
10. No in-repo HTTP LLM API.
11. **S5 chains must be decidable; S6/S7 core rules must be adjudicable**: object + condition + user-visible effect + concrete anchors — no empty field templates.
12. Ban template filler (“applies when entering the business scenario”, “per later implementation”).
13. **S6 productization (source language)**: decision cards with stable labels `Confirmed rule / Open boundary / User-visible effect / Linked open items` (or source-language equivalents). Independent bold labels; nest details; never compress multi-branch outcomes into one semicolon bullet. Write `_deliver/<slug>/<slug>-source-brief.md`.
14. **S7 locale conversion**: rewrite S6 into `defaults.deliverable_locale` only — **no new semantics**. When locale is zh-CN: main prose in zh-CN; first use of glossary terms uses the bilingual anchor pattern (see `deliverable-locale-tokens.json` / `RUNBOOK.zh-CN.md`); English only for source names, `` `API` `` tokens, explained acronyms. Emit `…-domain-brief.md` (en) or the zh-CN locale-brief filename from the token map. Risk/split read **S7**.
15. **S6/S7 open-items index**: each item led by **Affects rule**, with nested open/needed, suggested owner, impact-if-resolved.
16. **S6/S7 layered reading**: domain-model summary uses bold labels + nested bullets; no multi-object mush sentences.
17. **S6/S7 structured detail fidelity**: mapping/enum/field/formula/window/copy tables from S1/S5 must remain queryable in `## Key details` or card `Details`; else open items.
18. **S7 reader language**: no pipeline-stage jargon / internal QA slang; shape from `s6-reader-language-policy.json` (applies to locale brief).
19. **S6/S7 required sections**: Overview & scope, Out of scope here, Domain model summary, Core business rules, Glossary, Open items, Provenance.
20. **Cross-domain layer**: S3 must emit `propositions` / proposition list; `decision-atoms` / `conflict-ledger` are derived audit views only.
21. **S2 primary-facet recheck**: even with `primary_facet_to_slug`, re-check title/path `route_overrides` for cross-slug; body co-occurrence alone must not reassign.
22. **S3 cross-slug handoff**: when S2 reassigns, emit `CROSS_SLUG_HANDOFF.json|md`; Agent verifies absorption/downgrade/exclusion.
23. **S3 source set**: `_materialization_closure.json` is the only Compose source-set truth.
24. **S3.5**: prefer `decision_block + decision_confidence` on proposition items.
25. **S3 table-source signals**: long tables must be marked even without full propositions — do not drop silently.
26. **S4 primary inputs**: read propositions JSON/MD + cross-slug handoff first; `decision-atoms` are audit only.
27. **S4 domain model**: layered first-class objects / metrics-fields / display containers / relations / state machines / boundary candidates.
28. **S4 model gate**: `domain_model_quality.py` verifies structure; does not author prose.
29. **S5 chain mount**: every closed chain mounts on S4; chain objects ∈ first-class objects.
30. **S5 disposition**: place every `contract_candidate` / `evidence_note` / `noise_context` — never drop high-value evidence unexplained.
31. **S5 evidence promotion**: formulas, enums, visibility, windows, eligibility/reward effects → closed / half-closed / open — not auto-downgraded by candidate_type alone.
32. **S5 semantic remount**: Agent owns object vs noise judgment vs `strategy.md` + quality bar + S4 model.
33. **S5 half-closed split**: clear business rule vs unclear implementation — do not wholesale promote/demote; link open questions.
34. **S5 named structure protection**: named stages/tiers/states with business meaning must not vanish into “condition A/B/C”.
35. **S5 semantic normalize**: one chain ↔ one decision object; merge duplicate containers.
36. **S5 order normalize**: remount to business execution order; if keeping source order, justify; S6 does not re-judge order.
37. **S5 organization plan**: write `## Organization order` before chains; chain IDs/titles must match.
38. **S5 whole-draft order consistency**: one business spine across sections; organization order is sole chain-order truth.
39. **S5 open-question cross-links**: mutual links between chains and questions with decision impact.
40. **S5 boundary demotion**: noise/engineering must not appear as domain objects.
41. **S5 model layering**: metrics/fields/cards stay in metrics or display containers.
42. **S5 model–chain consistency**: chain objects cannot be metrics/pages/APIs.
43. **S5 work-draft gate**: `s5_work_draft_quality.py` verifies explicit form only.
44. **S5 required structure**: Input disposition · Domain model · Organization order · Closed decision chains · Open critical questions.
45. **S5 structured-detail handoff**: `## Structured detail handoff` is the only S6 detail source.
46. **S5 detail granularity triad**: full expand / lossless compress / open — never fake-complete.
47. **S5 no pseudo-closed**: ban placeholder wording; one cluster ↔ one decision question.
48. **S5 source coverage**: high-contribution S3 sources must be cited in S5.
49. **S5/S6 authoring contract**: read `distill-authoring-contract.md` before write.
50. **Constraint source**: Skill + strategy + quality bar + authoring contract dominate; scripts verify only.
51. **S2 stop before Compose**: checklist still containing `pending` rows blocks S3 (unless explicit override).
