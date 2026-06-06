<!-- agency-generated: v1 -->
---
name: subagent
description: Use when a unit of work should be composed as subagent-driven development — isolating a task to a dispatched subagent that returns a verified result.
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---

# subagent capability

Subagent composes subagent-driven development: a self-contained task is dispatched into a clean context and its verified result returns to the orchestrator.

## When to use

- A self-contained task suited to a dispatched subagent
- Work whose context is heavy enough to isolate from the main thread

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `develop` | effect | Dispatch a worker child via delegate, then gate it spec-review→quality-review; done iff both pass. | [details](references/develop.md) |

## Example

```bash
await call_tool('capability_subagent_develop', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- (none documented)
