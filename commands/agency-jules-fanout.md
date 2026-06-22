---
description: Walk the `jules-fanout` discipline — `/agency-jules-fanout` drives `develop.skill_walk(name='jules-fanout')`, delivering ONE phase at a time and recording the SkillRun provenance (Spec 018 Win 1).
---

## `/agency-jules-fanout` — walk the `jules-fanout` discipline

Phases: plan-batch → fan-out → join

Each phase records a `Phase` node and the SkillRun `SERVES` the active Intent; the engine pauses at hard gates.

| # | Phase | Input | Output | Verbs | Gate |
|---|-------|-------|--------|-------|------|
| 1 | plan-batch | — | items | — |  |
| 2 | fan-out | driver, driver_verb, items, quota | fanout_result | — |  |
| 3 | join | — | child_outcomes | — | hard |

```python
await call_tool('capability_develop_skill_walk', {'name': 'jules-fanout', 'inputs': {}})
```

Resume after a paused gate with `resume_from='<skill_id>'` and the gate's `resume_with` keys. Status contract: `completed | input-required | failed`.

