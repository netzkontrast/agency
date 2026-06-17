---
name: persona
description: "Use when a task needs a specific engineering specialist's lens — architecture,"
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---
<!-- agency-generated: v1 -->

# persona capability

A native reimplementation of SuperClaude's specialist agents (architects, engineers, analysts, mentors) as a built-in, dispatchable persona registry — NOT ingested prompt files. Decidable: a task is matched to the right specialist by domain, and a dispatch brief (role + focus + approach + task) is composed and recorded as provenance. Pairs with `panel` (business experts) and `subagent` (the dispatch machinery).

## When to use

- A task that maps to a named specialist (architect, security, performance, QA)
- An ambiguous task that should be routed to the right expert first
- Composing a focused subagent dispatch from a specialist role

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `list` | act | The specialist-persona roster — name · focus · approach. | [details](#list) |
| `recommend` | act | Recommend the specialist persona(s) best matched to a ``task`` by decidable domain overlap (read-only). | [details](#recommend) |
| `summon` | effect | Summon a specialist — compose a dispatch brief + record provenance (Spec 297). | [details](references/summon.md) |

## Example

```bash
await call_tool('capability_persona_list', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- Generic dispatch for a security-critical task → summon the security-engineer
- Building before requirements are concrete → summon the requirements-analyst

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`specialist-dispatch`** (discipline): match → brief → dispatch → verify
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'specialist-dispatch', 'inputs': {}, 'intent_id': '…'})`

## list

The specialist-persona roster — name · focus · approach.

Parameters: `()`.

_(Tier B — verb docstring lacks Spec 016 Inputs:/Returns:/chain_next: markers; reference is in-skill only. Add markers to upgrade to a separate references/list.md.)_

## recommend

Recommend the specialist persona(s) best matched to a ``task`` by decidable domain overlap (read-only).

Parameters: `(task: 'str', top: 'int' = 3)`.

_(Tier B — verb docstring lacks Spec 016 Inputs:/Returns:/chain_next: markers; reference is in-skill only. Add markers to upgrade to a separate references/recommend.md.)_
