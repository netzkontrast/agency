<!-- agency-generated: v1 -->
---
name: select
description: Use when an operation could be done several ways and the right approach depends
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---

# select capability

A native, generalized reimplementation of SuperClaude's `sc-select-tool`: score an operation's complexity and route it to the right approach archetype — `semantic` (structure-aware, accurate), `pattern` (fast bulk edits), or `native` (safe default). Decidable (like `panel`/`mode`); records the choice as provenance. Answers a different question than `delegate.dispatch_decision` (inline-vs-dispatch): *which approach* for the operation.

## When to use

- A refactor/edit operation whose approach is not obvious
- A bulk transformation where speed vs precision matters
- A routing decision between structure-aware and pattern-based tooling

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `archetypes` | act | The approach archetypes + their trade-offs. | [details](#archetypes) |
| `route` | effect | Route an ``operation`` to an approach archetype by decidable complexity scoring (Spec 296). | [details](references/route.md) |

## Example

```bash
await call_tool('capability_select_archetypes', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- Bulk-editing across many files with a symbol tool → route to pattern
- Renaming a symbol with blind find-replace → route to semantic

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`select-usage`** (usage): use-effect → use-act → confirm
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'select-usage', 'inputs': {}, 'intent_id': '…'})`

## archetypes

The approach archetypes + their trade-offs.

Parameters: `()`.

_(Tier B — verb docstring lacks Spec 016 Inputs:/Returns:/chain_next: markers; reference is in-skill only. Add markers to upgrade to a separate references/archetypes.md.)_
