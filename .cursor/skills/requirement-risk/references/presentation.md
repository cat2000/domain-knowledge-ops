# requirement-risk · presentation contract

> Stacks with [`.cursor/rules/requirement_risk.md`](../../../rules/requirement_risk.md): substance (class/severity/keys) from the rule; readability from this file.  
> Spoken deixis: [`../../_shared/presentation-p10.md`](../../_shared/presentation-p10.md).  
> Chinese locale: [`presentation.zh-CN.md`](./presentation.zh-CN.md).

## Essence

The report is **sprint decision input**. Optimize **decision latency**.

## Laws P1–P9

| # | Law | Why |
|---|-----|-----|
| P1 | **Summary answers “what” first**: **Scope** states user-visible capability/pages/boundaries (P10), then must-decide items | Readers must not reverse-engineer scope from R items |
| P2 | **User-visible headings in reader language** (often zh-CN for stakeholders): `## Summary`; English keys only as parenthetical subtitles | Lower product/biz reading cost |
| P3 | Keep `#### R-00N · severity · topic` (validator depends on it); topic in plain language | Traceable + scannable |
| P4 | Conflicts (ticket vs design vs brief) → narrow ≤4-col table under Evidence: `Source \| Claim \| To decide` | Tables beat long prose |
| P5 | **Stakes** ≤2 short bullets: user-visible / delivery consequence | Lower decode cost |
| P6 | MUST items add **Suggested owner** (role, not invented names) in disposition | Meeting-assignable |
| P7 | Boundaries already clear in briefs → demote or mark “aligned with library”; conflicts only get `[DOMAIN_KNOWLEDGE]` | Avoid duplicate MUST on known rules |
| P8 | **`brief` mode**: `## Summary` + `EVIDENCE_COVERAGE` only; summary still has Scope, must-decide, counts, readiness | Stand-up short read |
| P9 | No meta (“readable edition”); do not explain Layer/R/D jargon to non-engineers | Structure is self-describing |

**P10**: [`../../_shared/presentation-p10.md`](../../_shared/presentation-p10.md).

## stage → depth

| stage | Summary | Layer 2 |
|-------|---------|---------|
| `intake` | Required; top MUST ≤5 | May omit full risk list; keep `EVIDENCE_COVERAGE` |
| `refinement` (default) | Required | Full risk list + acceptance testability |
| `pre_sprint` | Required | Full + MUST owners + governance fields |

## Recommended summary

```markdown
## Summary

**Scope**: … (one sentence: capability / pages / not doing)

**One-liner**: …

**Must decide first**: …

**Counts**: MUST N · SHOULD N · optional N
**Readiness**: …
```

Count separators `·` or `/` are fine; must reconcile with R titles.
