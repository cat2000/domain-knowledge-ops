# Offline demo fixture (no Atlassian required)

Fictional **Acme Orders** sample so you can try `@requirement-risk` / `@ticket-splitter` / `@ticket-test-design` without credentials or network.

Full narrative (Paths A–C): [`../../../WALKTHROUGH.md`](../../../WALKTHROUGH.md).  
Industry map (strategy → modules → this brief): [`INDUSTRY.md`](./INDUSTRY.md).

## Try in 60 seconds

Open this repo in Cursor, then:

```text
@requirement-risk DEMO-1 team=demo
@ticket-splitter DEMO-1 team=demo
@ticket-test-design DEMO-1 team=demo
```

## What the Agent must do (offline path)

When the issue key matches `DEMO-*` (or the user says `offline` / `fixture`):

1. **Do not** call Jira REST / MCP / `fetch_jira_attachments.py`.
2. Read the ticket from `jira/DEMO-1.md` (this folder).
3. Read attribution from `jira/DEMO-1.attribution.yaml`.
4. Treat curated root as **this folder’s** `curated/by-root/100001/` (not the empty production `domain-knowledge/curated/by-root/`).
5. Primary brief (English SSOT): `curated/by-root/100001/_deliver/ordering/ordering-domain-brief.md`. A zh-CN locale sibling ships alongside it: `ordering-领域知识定稿.md`.
6. Still run the usual validate scripts on the draft report / split / test-design output.

## Layout

```text
fixtures/offline-demo/
  README.md                 ← this file
  jira/DEMO-1.md
  jira/DEMO-1.attribution.yaml
  curated/by-root/100001/
    DOMAIN_MODULE_CHECKLIST.md
    _deliver/ordering/ordering-domain-brief.md      ← English SSOT
    _deliver/ordering/ordering-领域知识定稿.md        ← zh-CN locale sibling
```

`root_id` `100001` matches the shipped `demo` team in `team-roots.json`.
