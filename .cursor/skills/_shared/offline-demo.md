# Offline demos (`DEMO-*` / `DEMO-BILL-*`) · shared

> Used by `@requirement-risk`, `@ticket-splitter`, and `@ticket-test-design`.

## Triggers

| Key / cue | Fixture root |
|-----------|----------------|
| `DEMO-1` / `DEMO-*` (default Acme Orders) | `domain-knowledge/fixtures/offline-demo/` |
| `DEMO-BILL-*` (SaaS billing portability sample) | `domain-knowledge/fixtures/saas-billing/` |
| User says `offline` / `fixture` / points at a fixture folder | That folder |

## Agent rules

1. **No network**: do not call Jira REST, Atlassian MCP, or `fetch_jira_attachments.py`.
2. **Ticket body**: `<fixture>/jira/<KEY>.md`
3. **Attribution**: `<fixture>/jira/<KEY>.attribution.yaml` (if present)
4. **Curated root**: `<fixture>/curated/by-root/100001/`  
   (override normal `domain-knowledge/curated/by-root/<root_id>/` for this run)
5. **Team**: treat as `demo` / root `100001` unless user overrides.
6. **Gates still apply**: write draft under `.jira_attachments/<KEY>/` if useful, then run the same validate scripts.
7. In `EVIDENCE_COVERAGE` / notes, state **`source=offline-fixture`** and which fixture folder.

Details:

- Acme Orders: [`../../../domain-knowledge/fixtures/offline-demo/README.md`](../../../domain-knowledge/fixtures/offline-demo/README.md)
- SaaS billing: [`../../../domain-knowledge/fixtures/saas-billing/README.md`](../../../domain-knowledge/fixtures/saas-billing/README.md)
