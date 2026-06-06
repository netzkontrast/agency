<!-- agency-generated: v1 -->
---
name: delegate
description: Use when a task might be better handled by a subagent (local, Jules, or another driver) and the choice to dispatch versus stay inline must be weighed, then work fanned out and the results joined.
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---

# delegate capability

Delegate weighs the token-economics and safety signals of dispatching, fans a task out to one or more drivers, and reduces their results back into a single answer.

## When to use

- A task large or parallelizable enough to consider delegating
- Several independent sibling tasks that could run concurrently
- Uncertainty whether to dispatch a subagent or work inline

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `dispatch_bash_hints` | transform | Compose the bash-hint context block for a dispatch prompt. | [details](references/dispatch_bash_hints.md) |
| `dispatch_decision` | transform | Apply the dispatch-vs-inline heuristic and return a recommendation. | [details](references/dispatch_decision.md) |
| `fan_out` | effect | Open one child Lifecycle per item (capped at `quota`), dispatch the driver for each, and record a Delegation that DELEGATES_TO every child. | [details](references/fan_out.md) |
| `join` | act | Reduce a delegation over its children's Lifecycle state. | [details](references/join.md) |

## Example

```bash
await call_tool('capability_delegate_dispatch_bash_hints', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- Dispatching without weighing the cost → check capability_delegate_dispatch_decision first
- Spawning siblings then losing their results → reduce with capability_delegate_join
