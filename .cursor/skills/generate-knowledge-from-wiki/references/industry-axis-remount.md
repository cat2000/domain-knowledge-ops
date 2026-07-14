# Axis landing & write-through (essence)

> Load when S2 tagging or S4–S7 compose risks mistaking **source layout** for **domain cuts**.  
> English SSOT. No tenant product-surface names here — those are probe examples, not pack rules.

## Essence

```text
S7 usefulness ≈ industry axes × land-in-axes × write-through × confirm gates
```

| Piece | Means | Not |
|-------|--------|-----|
| **Industry axes** | `strategy.md` §2 / profiles = adjudication questions | Coverage already done; product folder names as modules |
| **Land-in-axes** | Every accepted source lands in an existing axis slug (or a human-confirmed new slug) | Promoting app/channel/facet/product-line directories into checklist rows |
| **Write-through** | Landed business propositions become S7 `### 规则`/`### Rule` or explicit Open items | Closure tagged but brief empty / thin while sources exist |
| **Confirm gates** | Confirm only with tagged sources; ship only when write-through passes (`tagging_acceptance --after-s7`) | Confirming empty rows; shipping zero-rule “covered” briefs |

```text
Source layout (wiki tree / app / channel / facet)
        ↓  land (S2 closure → existing axis)
Industry axis slug
        ↓  write through (S3→S7)
Rule card  or  Open item
```

## Agent algorithm (tenant-agnostic)

1. **Axes are fixed until strategy changes.** Do not invent parallel module trees from how Confluence or Jira is filed.
2. **Land first, slug later.** For each page/ticket: ask which **strategy axis** owns the user-visible commitment. Put closure there. Propose a **new** slug only if no axis fits — show as **pending**, wait for human confirm.
3. **Surface labels are not domains.** Channel / app / gateway / folder / `facet-*` may stay as provenance or `product_line` tags; they must not become default `_deliver/` modules.
4. **Write through or leave pending.** After Compose, `pages_with_props` with business content must map to rule cards or Open items. Confirmed + sources + zero rules = process failure → revert confirm.
5. **Measure, don’t enumerate specials.** Use `tagging_acceptance.py` (closure / Jira half / `--after-s3` / `--after-s7 --strict`). Do not maintain a hard-coded product→slug table in this pack.

## Forbidden

- Hard-coding tenant product names (apps, shells, contests, gateways) into reusable skills or scripts as remount “defaults”
- Recreating source-tree modules so row counts match an old brief library
- Claiming “template confirmed = knowledge covered”

## Related

- `scripts/distill/tagging_acceptance.py` (measurable gates only)
- [`iron-laws.md`](./iron-laws.md) §4a–4e
