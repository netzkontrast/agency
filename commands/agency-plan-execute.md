---
description: Walk the `plan-execute` discipline — `/agency-plan-execute` drives `develop.skill_walk(name='plan-execute')`, delivering ONE phase at a time and recording the SkillRun provenance (Spec 018 Win 1).
---

## `/agency-plan-execute` — walk the `plan-execute` discipline

Phases: frame → draft-plan → plan-signoff → execute-step → checkpoint → synthesize

Drive the skill atomically — each phase records a `Phase` node and the SkillRun `SERVES` the active Intent; the engine pauses at hard gates.

```python
await call_tool('capability_develop_skill_walk', {'name': 'plan-execute', 'inputs': {}})
```

Resume after a paused gate with `resume_from='<skill_id>'` and the gate's `resume_with` keys. Status contract: `completed | input-required | failed`.

