---
description: Walk the `quality-sweep` discipline — `/agency-quality-sweep` drives `develop.skill_walk(name='quality-sweep')`, delivering ONE phase at a time and recording the SkillRun provenance (Spec 018 Win 1).
---

## `/agency-quality-sweep` — walk the `quality-sweep` discipline

Phases: scope → decidable → judgment → score-report → remedy

Drive the skill atomically — each phase records a `Phase` node and the SkillRun `SERVES` the active Intent; the engine pauses at hard gates.

```python
await call_tool('capability_develop_skill_walk', {'name': 'quality-sweep', 'inputs': {}})
```

Resume after a paused gate with `resume_from='<skill_id>'` and the gate's `resume_with` keys. Status contract: `completed | input-required | failed`.

