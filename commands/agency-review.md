---
description: Walk the `review` discipline — `/agency-review` drives `develop.skill_walk(name='review')`, delivering ONE phase at a time and recording the SkillRun provenance (Spec 018 Win 1).
---

## `/agency-review` — walk the `review` discipline

Phases: request → dispatch → resolve

Each phase records a `Phase` node and the SkillRun `SERVES` the active Intent; the engine pauses at hard gates.

| # | Phase | Input | Output | Verbs | Gate |
|---|-------|-------|--------|-------|------|
| 1 | request | — | context, diff | — |  |
| 2 | dispatch | driver, driver_verb, items | findings | — |  |
| 3 | resolve | — | addressed | — | hard |

```python
await call_tool('capability_develop_skill_walk', {'name': 'review', 'inputs': {}})
```

Resume after a paused gate with `resume_from='<skill_id>'` and the gate's `resume_with` keys. Status contract: `completed | input-required | failed`.

