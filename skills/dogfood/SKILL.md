<!-- agency-generated: v1 -->
---
name: dogfood
description: Use when recording or rendering observation ledgers in the graph — capturing a development note, exporting the graph for merge-recovery, or importing it back.
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---

# dogfood capability

Dogfood keeps observation ledgers graph-native: notes recorded as nodes, exported and imported as JSON preserving ids and validity windows, and rendered to markdown on demand.

## When to use

- An insight from a dev session worth keeping
- A graph that must survive a container or merge boundary
- A ledger that should render to markdown on demand

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `boundary_use_audit` | transform | Audit BoundaryUse nodes — flag raw-tool uses where a verb exists (transform). | [details](references/boundary_use_audit.md) |
| `collect` | transform | Walk ``plan_dir`` for ``DOGFOOD-NOTES.md`` files; extract observations. | [details](references/collect.md) |
| `export` | effect | Dump the provenance store to a portable JSON file. | [details](references/export.md) |
| `import` | effect | Replay a JSON export into this graph, preserving ids + windows. | [details](references/import.md) |
| `note` | act | Record an observation Reflection tagged with plan_slug. | [details](references/note.md) |
| `record_decision` | effect | Bind a decision to the current session (effect). | [details](references/record_decision.md) |
| `render` | transform | Project plan_slug observations into DOGFOOD-NOTES.md. | [details](references/render.md) |

## Example

```bash
await call_tool('capability_dogfood_boundary_use_audit', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- Writing a markdown ledger by hand → record it via capability_dogfood_note
- Losing graph state across a container → capability_dogfood_export the graph

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`dogfood-usage`** (usage): use-transform → use-effect → use-act → confirm
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'dogfood-usage', 'inputs': {}, 'intent_id': '…'})`
