---
description: Walk the `specialist-dispatch` discipline — `/agency-specialist-dispatch` drives `develop.skill_walk(name='specialist-dispatch')`, delivering ONE phase at a time and recording the SkillRun provenance (Spec 018 Win 1).
---

## `/agency-specialist-dispatch` — walk the `specialist-dispatch` discipline

Phases: match → brief → dispatch → verify

Drive the skill atomically — each phase records a `Phase` node and the SkillRun `SERVES` the active Intent; the engine pauses at hard gates.

```python
await call_tool('capability_develop_skill_walk', {'name': 'specialist-dispatch', 'inputs': {}})
```

Resume after a paused gate with `resume_from='<skill_id>'` and the gate's `resume_with` keys. Status contract: `completed | input-required | failed`.

