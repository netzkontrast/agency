---
description: Walk the `capability-routing` discipline — `/agency-capability-routing` drives `develop.skill_walk(name='capability-routing')`, delivering ONE phase at a time and recording the SkillRun provenance (Spec 018 Win 1).
---

## `/agency-capability-routing` — walk the `capability-routing` discipline

Phases: frame → rank → select → confirm

Drive the skill atomically — each phase records a `Phase` node and the SkillRun `SERVES` the active Intent; the engine pauses at hard gates.

```python
await call_tool('capability_develop_skill_walk', {'name': 'capability-routing', 'inputs': {}})
```

Resume after a paused gate with `resume_from='<skill_id>'` and the gate's `resume_with` keys. Status contract: `completed | input-required | failed`.

