---
name: document
description: "Use when a repository's structure must be understood or rendered — an explanation of a subsystem, a project index, or a graph-native rendering — without loading the whole tree."
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---
<!-- agency-generated: v1 -->

# document capability

Document renders graph-native briefings: an index of a repo, an explanation of a subsystem, or a markdown rendering produced on demand from the graph. index_repo sources its file list + per-file symbol counts from the codegraph index (`codegraph files`); to locate code inside a subsystem, query codegraph first — `codegraph explore "<area>"` (source + call paths in one call) / `codegraph node <file>` (a file + its dependents) — before reading files.

## When to use

- An unfamiliar codebase that needs onboarding
- A stale mental model of a tree untouched for weeks
- A subsystem whose purpose is unclear from the files alone
- Locating code within a subsystem → `codegraph explore "<area>"` / `codegraph node <file>` before reading files

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `convergence` | act | Audit a Document's convergence facets (Spec 292 C3). | [details](references/convergence.md) |
| `emit` | effect | Persist ARBITRARY rendered content as a round-trippable Document (Spec 292). | [details](references/emit.md) |
| `explain` | act | Deterministically explain code as markdown, emitting a Reflection. | [details](references/explain.md) |
| `index_repo` | effect | Deterministic repo briefing. | [details](references/index_repo.md) |
| `ingest` | effect | Round-trip a markdown file INTO the graph (file → graph; Spec 292). | [details](references/ingest.md) |
| `mirror` | effect | Project graph→file AND event-source it (Spec 292 — closes the loop). | [details](references/mirror.md) |
| `render` | transform | Deterministically project graph state to markdown. | [details](references/render.md) |
| `reopen` | effect | Reopen an archived session Document — reconstruct the four concepts (Spec 292 C4). | [details](references/reopen.md) |
| `restore_session` | act | Restore a complete session from the Session Graph (Spec 292). | [details](references/restore_session.md) |
| `revisions` | act | Read a Document's keep-both revision history (Spec 292). | [details](references/revisions.md) |
| `session` | effect | Render a Session as a Document — the four concepts converge (Spec 292). | [details](references/session.md) |
| `session_analytics` | act | Cypher analytics over the Session Graph (Spec 292). | [details](references/session_analytics.md) |
| `sync` | effect | Ingest every CHANGED markdown file under ``path`` (Spec 292). | [details](references/sync.md) |

## Example

```bash
await call_tool('capability_document_convergence', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- Reading every file to grasp a repo → index it via capability_document_index_repo
- Guessing a subsystem's role → get capability_document_explain output
- grep/Read loop to find code while `.codegraph/` exists → `codegraph explore`/`query` already indexed it

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`repo-briefing`** (discipline): scope → scan → render → publish
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'repo-briefing', 'inputs': {}, 'intent_id': '…'})`
  1. **scope** — Fix the repo path + the token budget.
     Name the root to brief and the max-tokens budget for the preview. The budget governs the preview only — a SAVED index is never truncated (it must not lie about the tree).
  2. **scan** — Scan the tree into a structured index.
     Walk the package tree — entry points, modules, notable patterns, recent reflections — into a recorded index. Capture every module; never drop entries to fit a budget.
  3. **render** — Render the briefing markdown.
     Render the index to the PROJECT_INDEX briefing — short fixed sections first (so they survive a budget), then the macro structure.
  4. **publish** — Write the briefing in FULL.
     On save the index renders in FULL — every module survives, no omission marker. Confirm this gate only when the saved briefing is complete.
