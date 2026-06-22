---
description: Walk the `plan-execute` discipline — `/agency-plan-execute` drives `develop.skill_walk(name='plan-execute')`, delivering ONE phase at a time and recording the SkillRun provenance (Spec 018 Win 1).
---

## `/agency-plan-execute` — walk the `plan-execute` discipline

Phases: frame → draft-plan → plan-signoff → execute-step → checkpoint → synthesize

Each phase records a `Phase` node and the SkillRun `SERVES` the active Intent; the engine pauses at hard gates.

| # | Phase | Input | Output | Verbs | Gate |
|---|-------|-------|--------|-------|------|
| 1 | frame | — | requirements | `intent.decompose`, `intent.assumptions` |  |
| 2 | draft-plan | title, steps | plan | — |  |
| 3 | plan-signoff | — | user_confirmed | — | hard |
| 4 | execute-step | — | step_results | `delegate.dispatch_decision` |  |
| 5 | checkpoint | — | reviewed | — | hard |
| 6 | synthesize | — | summary | — | hard |

```python
await call_tool('capability_develop_skill_walk', {'name': 'plan-execute', 'inputs': {}})
```

Resume after a paused gate with `resume_from='<skill_id>'` and the gate's `resume_with` keys. Status contract: `completed | input-required | failed`.

### Verbs invoked (full params one-deep)

- `intent.decompose` → `skills/intent/references/decompose.md`
- `intent.assumptions` → `skills/intent/references/assumptions.md`
- `delegate.dispatch_decision` → `skills/delegate/references/dispatch_decision.md`

