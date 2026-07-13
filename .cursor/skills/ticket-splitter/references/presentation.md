# ticket-splitter · presentation contract

> Stacks with [`.cursor/rules/ticket_system.md`](../../../rules/ticket_system.md): substance from the rule; readability from this file.  
> Spoken deixis: [`../../_shared/presentation-p10.md`](../../_shared/presentation-p10.md).  
> Chinese locale: [`presentation.zh-CN.md`](./presentation.zh-CN.md).

## Essence

Items are **iteration-ready commitments**. Readers need “how many slices, suggested order, how to verify” before field detail.

**Title**: 3-second headline of the promised outcome — **not** a comma-joined dump of every `scope` change. One primary result in the title; the rest in `scope` / `done_when`.

**scope**: each bullet is **one speakable concern** — not a PRD field table welded with colons/semicolons/slashes.

## Laws P1–P12

| # | Law | Why |
|---|-----|-----|
| P1 | Open with one **Scope** sentence (same as risk; say what you do, not “this ticket’s scope”) | Boundary before items |
| P2 | **done_when** = observable behavior; ban “dev done” | INVEST / testable |
| P3 | If source weakens testability → **correction note** first, then Spike/Story/Enabler | Correct before split |
| P4 | No preamble explaining ticket_system to the reader | Less noise |
| P5 | After Scope, `## Split overview` (3–5 lines): count, order, blocking Spike?, optional Enablers | 30s planning read |
| P6 | Correction notes are narrative paragraphs; keep (a)(b)(c) internal — do not print letter tags | Lower jargon barrier |
| P7 | If same-session `@requirement-risk` or open conflicts → cite `R-00N` on Spike/Story | Trace risk→split |
| P8 | Optional Tech Task (Enabler) titles mark `(optional)`; `brief` omits Enabler detail | Avoid false must-dos |
| P9 | Item labels: reader-language heading + English key in parentheses | Bilingual scan |
| P11 | **Title one-breath readable**: one primary result; ban piled enumeration via list-separator commas / “and” conjunctions stacking multiple changes; ban empty verbs / private abbreviations | Title = commitment headline |
| P12 | **scope one idea per bullet**: ban `covers X: A; B / C / D` welding | Speakable boundaries |

**P10**: [`../../_shared/presentation-p10.md`](../../_shared/presentation-p10.md).

## Title one-breath (P11)

Self-check: can a refinement audience **say the primary outcome in one breath**?

| Do | Don’t |
|----|-------|
| One primary result (object + observable outcome) | Stack three changes with list-separator commas / `and` in the title |
| Secondary changes in `scope` or one subordinate clause | Compress three scope bullets into the title |
| Full spoken words | Private abbreviations |
| Concrete verbs: change / enable / remove / let users… | Empty verbs: open / empower / complete (no object) |

## scope one idea (P12)

Self-check: can listeners **restate this bullet without switching topics mid-sentence**?

| Do | Don’t |
|----|-------|
| One bullet = one concern | Weld controls into `covers X: A; B / C / D` |
| Enumerations as whole sentences or separate bullets | Slash-chains mixing badges + filters + counts |
| Multi-field cards as short sentences, not semicolon mash | Three themes welded by semicolons |

## Field labels (P9)

Reader-facing heading in the deliverable's locale + English key in parentheses. For English output use the English label directly (`Title`, `Scope`, `Acceptance`, `Depends`, `Confidence`); for zh-CN output use the zh-CN reader labels defined in [`presentation.zh-CN.md`](./presentation.zh-CN.md) §Field labels.

| English reader label | English key (rule) |
|-----------------------|--------------------|
| Title | title |
| Scope | scope |
| Acceptance | done_when |
| Depends | depends_on |
| Confidence | confidence |

Item type titles: `Spike N` / `User Story N` / `Tech Task N (Enabler · optional)`.

## Recommended structure

```markdown
**Scope**: …

## Split overview
- N items: Spike 1 → User Story 1 → …
- Blocking: …
- Optional: Tech Task 1 (Enabler) only if backend integration needs it

**Correction note** (only when INVEST needs correction; narrative; no (a)(b)(c) tags)
…

Spike 1 / User Story 1 / …
```

**`brief` mode (P8)**: Scope + Split overview + correction note only; gate with `--brief`.
