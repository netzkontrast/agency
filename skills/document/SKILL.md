<!-- agency-generated: v1 -->
---
name: document
description: Use when a repository's structure must be understood or rendered — an explanation of a subsystem, a project index, or a graph-native rendering — without loading the whole tree.
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---

# document capability

Document renders graph-native briefings: an index of a repo, an explanation of a subsystem, or a markdown rendering produced on demand from the graph.

## When to use

- An unfamiliar codebase that needs onboarding
- A stale mental model of a tree untouched for weeks
- A subsystem whose purpose is unclear from the files alone

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `explain` | act | Deterministic code → markdown explanation; emits a Reflection. | [details](references/explain.md) |
| `index_repo` | effect | 94%-reduction repo briefing — deterministic; ≤ max_tokens. | [details](references/index_repo.md) |
| `render` | transform | Project graph state to markdown; deterministic. | [details](references/render.md) |

## Example

```bash
await call_tool('capability_document_explain', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- Reading every file to grasp a repo → index it via capability_document_index_repo
- Guessing a subsystem's role → get capability_document_explain output

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`repo-briefing`** (discipline): scope → scan → render → publish
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'repo-briefing', 'inputs': {}, 'intent_id': '…'})`
