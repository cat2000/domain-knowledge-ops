# team → library → root_id

> **SSOT**: `domain-knowledge/jira/team-roots.json` (**v3**: `libraries` + `teams` mounting them)  
> Open-source default ships **one** `demo` library and team. Path C = single mount. Add more `libraries.*` / `teams.*` as needed.

| team | libraries | primary root_id | display_name |
|------|-----------|-----------------|--------------|
| demo | demo | 100001 | Demo Product Team |

Aliases: `default`. Also `root-id=100001` or `board_id=1`.

Optional `defaults.default_team` / `defaults.default_library` (currently `demo`).  
See [`docs/TEAM_ROOTS_V3.md`](../../../docs/TEAM_ROOTS_V3.md).
