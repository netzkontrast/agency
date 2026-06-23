---
name: select
description: "Use when an operation could be done several ways and the right approach depends"
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---
<!-- agency-generated: v1 -->

# select capability

A native, generalized reimplementation of SuperClaude's `sc-select-tool`: score an operation's complexity and route it to the right approach archetype — `semantic` (structure-aware, accurate), `pattern` (fast bulk edits), or `native` (safe default). Decidable (like `panel`/`mode`); records the choice as provenance. Answers a different question than `delegate.dispatch_decision` (inline-vs-dispatch): *which approach* for the operation.

## When to use

- A refactor/edit operation whose approach is not obvious
- A bulk transformation where speed vs precision matters
- A routing decision between structure-aware and pattern-based tooling

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `archetypes` | act | The approach archetypes + their trade-offs. | [details](references/archetypes.md) |
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

- **`approach-routing`** (discipline): characterize → weigh → route → commit
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'approach-routing', 'inputs': {}, 'intent_id': '…'})`
  1. **characterize** — Characterize the operation + its scope.
     Name what kind of operation this is and how big — the inputs that decide which approach fits (one-off vs repeated, small vs broad).
  2. **weigh** — Weigh the candidate approaches.
     Enumerate the viable approaches and their tradeoffs for this operation + scope. Don't anchor on the first one that comes to mind.
  3. **route** — Route to the best-fit approach.
     Choose the approach whose tradeoffs best match the characterised operation; name the deciding factor.
  4. **commit** — Commit to the approach with rationale.
     State why this approach wins given the operation + scope. Confirm this gate only with a grounded rationale, not a preference.
