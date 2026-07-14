# Industry-axis remount (keep adjudication axes)

> Load when S2 tagging or S4–S7 compose risks dropping product-surface wiki density.  
> English SSOT. Do **not** recreate Mall / Hui / Gateway / Messaging as default modules unless the human **changes strategy §2**.

## Principle

**Industry axes stay.** Wiki is often written by app/channel. Bidirectional tagging must **remount** those pages into axes (ordering / membership / compensation / claims / returns / …), then Compose must **write through** into S7 rules or Open items.

```text
Product-surface page  →  remount into industry slug  →  S7 rule card or Open item
```

## Remount map (default)

| Dense wiki / legacy theme | Prefer industry axis |
|---------------------------|----------------------|
| Mall catalog, cart limits, first-order, IOR coupon | `ordering-fulfillment` (eligibility-only → `membership-eligibility`) |
| Checkout session/node, FPV, pending pay, promo hold | `ordering-fulfillment` |
| Hui shell, CBP home cards, Pacesetter UI | `membership-eligibility` and/or `compensation-performance` |
| Milestone / Super Expanding / contest state matrices | `compensation-performance` |
| Privacy gate, password reset, rebind, title tables | `membership-eligibility` (or a **human-confirmed** new identity slug) |
| Message center / templates / read-unread (user-visible) | nearest axis that owns the trigger; else Open items |
| Gateway auth / SDK-only | appendix / non-business unless it changes a visible commitment |
| Autoship plan rules | `autoship-renewal` (pending until sources exist) |
| Returns / quality complaints | `returns-quality` (pending if no business propositions) |

## Agent duties

1. **S2**: when scanning unmatched / app-titled pages, assign closure to an **existing industry slug** first; propose a **new** slug only if no axis fits and show it on the checklist as pending.
2. **S3–S5**: do not drop high-causality contest/Mall/identity propositions because the facet name looks like an old product module.
3. **S6/S7**: every remounted `contract_candidate` becomes a rule card or an Open item (“Affects rule”). Confirmed + sources + **zero** `### 规则` = fake coverage → revert confirm.
4. **Never** tell humans that “industry template = coverage done.”

## Related

- `scripts/distill/tagging_acceptance.py` (remount hints + `--after-s7` write-through gate)
- [`iron-laws.md`](./iron-laws.md) §4a–4e
