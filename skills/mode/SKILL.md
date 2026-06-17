---
name: mode
description: "Use when the way of working should shift for the task at hand — discovery,"
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---
<!-- agency-generated: v1 -->

# mode capability

A native reimplementation of SuperClaude's behavioral modes: postures that change HOW the agent operates. Decidable (like `panel`/`thinking`): trigger-term overlap selects the mode; activation returns the posture's behavioral rules and records a `ModeActivation` node, so a session's adopted postures are provenance.

## When to use

- A vague or exploratory request that needs discovery before building
- A meta-cognitive ask: inspect reasoning, reflect on a failed approach
- A multi-tool or multi-step operation that needs routing or phasing
- A brevity-constrained context that needs compressed output

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `activate` | effect | Activate a behavioral posture — return its rules + record provenance (Spec 295). | [details](references/activate.md) |
| `detect` | act | Rank the behavioral modes by decidable trigger overlap with ``context`` (read-only). | [details](#detect) |
| `list` | act | The behavioral-mode roster — name · purpose · behaviors · triggers. | [details](#list) |

## Example

```bash
await call_tool('capability_mode_activate', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- Diving into build on a vague request → activate brainstorming first
- Repeating a failed approach → activate introspection to inspect the reasoning

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`mode-usage`** (usage): use-effect → use-act → confirm
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'mode-usage', 'inputs': {}, 'intent_id': '…'})`

## detect

Rank the behavioral modes by decidable trigger overlap with ``context`` (read-only).

Parameters: `(context: 'str')`.

_(Tier B — verb docstring lacks Spec 016 Inputs:/Returns:/chain_next: markers; reference is in-skill only. Add markers to upgrade to a separate references/detect.md.)_

## list

The behavioral-mode roster — name · purpose · behaviors · triggers.

Parameters: `()`.

_(Tier B — verb docstring lacks Spec 016 Inputs:/Returns:/chain_next: markers; reference is in-skill only. Add markers to upgrade to a separate references/list.md.)_
