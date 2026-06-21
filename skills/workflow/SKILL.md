---
name: workflow
description: "Use when a spec must move through its development stages (draft → open →"
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---
<!-- agency-generated: v1 -->

# workflow capability



## When to use

- A new spec needs a state machine → open_spec
- A spec advances a stage and the transition must be guarded + recorded → move_spec
- "What's in /inprogress?" → board, answered from the graph

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `board` | transform | BOARD — the graph-native spec board: live SpecLifecycles grouped by their ``spec``-machine state (optionally filtered to one ``state``). | [details](references/board.md) |
| `move_spec` | effect | MOVE_SPEC — advance the spec's Lifecycle to ``to_state`` via ``ctx.lifecycle.move`` (the SOLE state writer — Spec 339; an illegal edge is rejected by the ``spec`` machine's transition table). | [details](references/move_spec.md) |
| `open_spec` | act | OPEN_SPEC — mint a SpecLifecycle (machine ``spec``, state ``draft``) for a spec ``Document``, ``TRACKS``-bound to it and SERVING the intent. | [details](references/open_spec.md) |

## Example

```bash
await call_tool('capability_workflow_board', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- Hand-editing a spec's ``status:`` / folder without advancing the Lifecycle → drift
- Moving open→inprogress before its ADR decisions are approved → the gate refuses
- Writing ``Lifecycle.state`` directly → only ``ctx.lifecycle.move`` may (Spec 339)

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`workflow-usage`** (usage): use-transform → use-effect → use-act → confirm
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'workflow-usage', 'inputs': {}, 'intent_id': '…'})`
