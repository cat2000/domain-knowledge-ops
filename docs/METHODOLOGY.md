# Methodology · Confirm-gated Compose

**Confirm-gated Compose** is the named loop this pack teaches:

1. **Ingest** faithful sources (Confluence / Jira).
2. **Recognize** modules; humans mark **confirm**.
3. **Compose** only confirmed slugs through **S3→S7**.
4. **Review** stories against **S7** briefs (`@requirement-risk`, `@ticket-splitter`).

How Domain Knowledge Ops turns Confluence (and optional Jira history) into **adjudicated domain briefs** for story review. This page is an index; authoritative detail lives in linked SSOT files.

## Goals

1. **Onboarding** — shorten time-to-effective contribution on a product domain.
2. **Story context** — surface ambiguity, boundaries, and risk **before** sprint churn.
3. **Discussion fuel** — connect known rules to new requirements with traceable evidence.

Human methodology and industry fill-in: [`domain-knowledge/strategy.md`](../domain-knowledge/strategy.md) (§1 purpose, §2 your industry context).

## Pipeline narrative

| Stage | Steps | Outcome |
|-------|-------|---------|
| **Ingest** | S1 (Confluence sync); Jira adds Ingest + Classify | Faithful `materialized/` + indexes |
| **Recognize** | S2 + human **confirm** | Module checklist + closure index |
| **Compose** | S3 → S4 → S5 → S6 → S7 | Aggregates → work draft → source brief → **locale brief** |

**S7** `*-domain-brief.md` files are the reader-facing deliverables. `@requirement-risk` and `@ticket-splitter` consume **S7**, not raw wiki pages.

Full contract: [`.cursor/contracts/domain-knowledge-pipeline-contract.md`](../.cursor/contracts/domain-knowledge-pipeline-contract.md).

## Quality bar

- **Business first** — rules, eligibility, branches, user-visible outcomes over ticket noise.
- **Thorough extraction** — business-relevant material under `materialized/` must be checkable in `curated/`.
- **Human gates** — module cuts require **confirm** before Compose; scripts verify structure, humans own semantics.
- **No translation in S1–S6** — locale conversion happens only at **S7**.

Baselines: [`domain-knowledge/distill-quality-bar.md`](../domain-knowledge/distill-quality-bar.md) · skeleton: [`domain-knowledge/distill-document-skeleton.md`](../domain-knowledge/distill-document-skeleton.md).

## Module cutting

1. Fill **strategy §2** (industry context) via `@setup-domain-ops`.
2. Derive `s2-domain-profiles.json` themes/facets — not from hard-coded repo tables.
3. **S2** Recognize proposes slug rows; humans mark **confirmed** or defer.
4. **continue** runs Compose only for **confirmed** slugs.

Example (fictional): [`domain-knowledge/strategy.example.md`](../domain-knowledge/strategy.example.md) · offline map: [`domain-knowledge/fixtures/offline-demo/INDUSTRY.md`](../domain-knowledge/fixtures/offline-demo/INDUSTRY.md).

## Story review layer

After **S7** briefs exist:

- **`@requirement-risk`** — readiness / decision blockers (reads briefs; does not write curated).
- **`@ticket-splitter`** — INVEST slices with `scope` and observable `done_when`.

Rules: [`.cursor/rules/requirement_risk.md`](../.cursor/rules/requirement_risk.md) · [`.cursor/rules/ticket_system.md`](../.cursor/rules/ticket_system.md).

## Learn by doing

| Path | Doc |
|------|-----|
| 60s offline | [`WALKTHROUGH.md`](../WALKTHROUGH.md) Path A |
| Industry map without Confluence | Path B · second industry Path B2 |
| Real tenant | Path C + [`FIRST-RUN.md`](../.cursor/skills/generate-knowledge-from-wiki/FIRST-RUN.md) |
| With vs without brief | [`BENCHMARK.md`](./BENCHMARK.md) |
| Sample outputs | [`demo/`](./demo/) |
| Multi-harness | [`HARNESS.md`](./HARNESS.md) |
| Publish checklist | [`MARKETPLACE.md`](./MARKETPLACE.md) |
