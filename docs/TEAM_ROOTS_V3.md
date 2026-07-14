# team-roots v3 draft — one space = one library; teams mount many

Status: **single-library Path C ready** — shipped `team-roots.json` / `team-roots.example.json` are **v3**; `@setup-domain-ops` writes v3; normalize still expands legacy v2 and flattens primary mount for callers. Full multi-library classify/risk (beyond primary mount) is still a later slice.

## Product model (target)

```text
Confluence Space A → Library A ─┐
Confluence Space B → Library B ─┼─→ Team (board_id)  may use / classify into several libraries
Confluence Space C → Library C ─┘
```

| Fact | Implication |
|------|-------------|
| Confluence is organized by **space** | **One space → one domain library** (one sync URL, one module set, one `_deliver/`) |
| Spaces may be team-local or cross-team | Sharing is via **which teams mount the library**, not by merging spaces |
| Jira is **one board per delivery team** | Team config is mainly `board_id` + **`libraries[]`** |
| Teams do different work | A board can read/supplement **multiple** libraries without forcing one mega-brief |
| Later (optional) | Extract a **common** library or a compose-across-libraries layer when duplication hurts |

**Deferred (not v3 default):** multi-space → one composed library (`sources[]`). Revisit only when product cuts truly share one adjudication language.

Today (v2): each `teams.<key>` owns both `root_id` + `jira.board_id` (1:1).  
This draft: **1 space = 1 library**; **1 team → N libraries**; **N teams may mount the same library**.

## Concepts

| Concept | Meaning | On disk |
|---------|---------|---------|
| **Library** | One Confluence space/overview → briefs | Same spirit as today’s `curated/by-root/<root_id>/` (`library_id` may equal `root_id`) |
| **Team** | One Jira board + list of libraries it uses | Ingest by `board_id`; classify into mounted libraries’ modules |
| **Mount** | `team.libraries: ["orders", "payments"]` | Risk/split and Jira classify resolve briefs from those libraries |

```text
libraries.orders      ← sync Space ORDERS once
libraries.payments    ← sync Space PAY once
       ↑ mount
teams.web.libraries = [orders, payments]
teams.api.libraries = [orders]
```

## JSON shape (`version: 3`)

Example: [`team-roots.v3.example.json`](../domain-knowledge/jira/team-roots.v3.example.json).

```json
{
  "version": 3,
  "defaults": {
    "deliverable_locale": "en",
    "atlassian_site": "https://your-site.atlassian.net",
    "default_team": "demo",
    "default_library": "demo"
  },
  "libraries": {
    "<library_key>": {
      "display_name": "…",
      "library_id": "<root_id or stable id>",
      "root_id": "<confluence_page_id>",
      "confluence_overview": "https://…/wiki/spaces/…/overview?homepageId=…",
      "space_key": "ORDERS",
      "s2_profile": "default",
      "deliver_by_proposition": {
        "<slug>": ["<dir>", "<file.md>"]
      }
    }
  },
  "teams": {
    "<team_key>": {
      "libraries": ["<library_key>", "…"],
      "display_name": "…",
      "aliases": [],
      "attribution_config": "domain-knowledge/jira/teams/<team_key>.json",
      "jira": {
        "board_id": 1,
        "board_name": "…",
        "agile_team": "…",
        "jql_base": "…"
      }
    }
  }
}
```

Notes:

- **Library has exactly one Confluence root** (one space / overview). No `sources[]` in v3 default.
- **`team.libraries`**: ordered list; first entry may be the default for ambiguous attribution.
- Shorthand: `"library": "orders"` allowed as alias for `"libraries": ["orders"]` when loading.
- Module map (`deliver_by_proposition`) stays on the **library**.
- Team has **no** Confluence URL — only board + mounts.

## Pipeline behavior

### 1. Wiki sync (one space → one library)

```text
@generate-knowledge-from-wiki <overview-URL>
```

1. Resolve URL / `root_id` → `library_key`.
2. S1 → Recognize → confirm → Compose for **that library only**.
3. On-disk: keep `curated/by-root/<root_id>/` for parity, or map `library_id` ↔ `root_id` 1:1.

### 2. Jira supplement (team → mounted libraries)

```text
@add-knowledge-from-jira team=<team_key>
```

1. Resolve team → `board_id` + `libraries[]`.
2. Ingest sprints from the board.
3. Classify each ticket onto a slug in **one of** the mounted libraries (attribution config + cues).
4. Write under that library’s `curated/by-root/<root_id>/jira/…` (or library path).

### 3. Story review

`@requirement-risk` / `@ticket-splitter` with `team=…` load briefs from **mounted libraries** only (not the whole site).

## Resolution rules

1. Overview URL / `root_id` → single library.
2. `team` / `board_id` → team → `libraries[]`.
3. Many teams may mount the same library (shared space across teams).
4. One team may mount many libraries (different business areas).

## Compatibility with v2

Expand each v2 team:

```text
libraries[key] = { root_id, confluence_overview, deliver_by_proposition, s2_profile, library_id: root_id }
teams[key]     = { libraries: [key], jira, attribution_config, aliases, display_name }
```

Demo `demo` / `100001` unchanged in behavior.

## Setup dialogue (slim)

Human inputs stay minimal. Strategy modules come from an **industry best-practice draft**, not a long questionnaire and not web scrape as SSOT.

```text
Company + business intro
    → Agent drafts strategy §2 / module cut (industry template)
    → Human confirm
    → Confluence space URL(s) → one library per space + sync
    → Jira board id(s) → team mounts libraries[]
```

| # | Ask | Writes |
|---|-----|--------|
| 1 | Atlassian `.env` if missing | `.env` |
| 2 | **Company / product name + short business intro** (industry, who the rules apply to, one-line in/out boundary) | Seed for strategy |
| 3 | Agent acts as industry expert: propose **3–8 modules** (name + axis) + light §2 draft; show as template | Draft `strategy.md` §2 |
| 4 | Human **confirm** / edit module table | profiles, seeds, `deliver_by_proposition` |
| 5 | Each Confluence **space overview URL** (+ optional name) | `libraries.*` (one space = one library) |
| 6 | Each delivery team: **board_id** + which **libraries** it mounts (default: libraries just added) | `teams.*` |

Then hand off:

```text
@generate-knowledge-from-wiki <space-overview-URL>
@add-knowledge-from-jira team=<team_key>
```

**Template vs truth:** the industry draft shapes *how you cut modules*. Rule text in briefs still comes from Confluence + Jira after sync/classify — never treat the template as product SSOT.

Adding a space = new library + sync.  
Adding a team = board_id + `libraries[]`.  
No “merge these spaces into one library?” in v3 default.

## Later evolution (out of scope for v3 default)

| Need | Possible follow-on |
|------|-------------------|
| Same rules duplicated across libraries | New `libraries.common` curated by humans, or extract skill |
| True multi-space single brief | Optional `compose_of: [libA, libB]` — only with confirm-gated merge |
| Site-wide search | Index across mounted libs for a team — read path only |

## Implementation order

1. Schema + example (this doc) — done  
2. Slim `setup-domain-ops` dialogue — done  
3. `registry.py`: v3 load + v2 expand; `libraries_for_team`, `library_for_root_id` — done  
4. Single-library Path C ≡ by-root + v3 JSON on disk / setup writes v3 — done  
5. Team mounts multiple libraries for risk/split + Jira classify — later  
6. Docs: WALKTHROUGH Path C, TEAM_KNOWLEDGE_BASE — done for single-lib  

## Non-goals (v3)

- Auto-merging multiple spaces into one `_deliver/`  
- Treating public web pages or generic industry text as **rule SSOT** (drafting module *cuts* from company intro is in scope; inventing adjudicated rules is not)  
- Multi-site Atlassian in one defaults block (keep one `atlassian_site`)  
