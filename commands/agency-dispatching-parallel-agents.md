---
description: Walk the `dispatching-parallel-agents` discipline — `/agency-dispatching-parallel-agents` drives `develop.skill_walk(name='dispatching-parallel-agents')`, delivering ONE phase at a time and recording the SkillRun provenance (Spec 018 Win 1).
---

## `/agency-dispatching-parallel-agents` — walk the `dispatching-parallel-agents` discipline

Phases: partition → dispatch → join → synthesize

Each phase records a `Phase` node and the SkillRun `SERVES` the active Intent; the engine pauses at hard gates.

| # | Phase | Input | Output | Verbs | Gate |
|---|-------|-------|--------|-------|------|
| 1 | partition | — | independent_domains | `delegate.dispatch_decision` |  |
| 2 | dispatch | — | delegations | `delegate.fan_out` |  |
| 3 | join | — | results | `delegate.join` |  |
| 4 | synthesize | — | merged_result | — | hard |

```python
await call_tool('capability_develop_skill_walk', {'name': 'dispatching-parallel-agents', 'inputs': {}})
```

Resume after a paused gate with `resume_from='<skill_id>'` and the gate's `resume_with` keys. Status contract: `completed | input-required | failed`.

### Verbs invoked (full params one-deep)

- `delegate.dispatch_decision` → `skills/delegate/references/dispatch_decision.md`
- `delegate.fan_out` → `skills/delegate/references/fan_out.md`
- `delegate.join` → `skills/delegate/references/join.md`

