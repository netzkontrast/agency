---
description: Walk the `quality-review` discipline — `/agency-quality-review` drives `develop.skill_walk(name='quality-review')`, delivering ONE phase at a time and recording the SkillRun provenance (Spec 018 Win 1).
---

## `/agency-quality-review` — walk the `quality-review` discipline

Phases: scope → decidable → judgment → score-report

Drive the skill atomically — each phase records a `Phase` node and the SkillRun `SERVES` the active Intent; the engine pauses at hard gates.

```python
await call_tool('capability_develop_skill_walk', {'name': 'quality-review', 'inputs': {}})
```

Resume after a paused gate with `resume_from='<skill_id>'` and the gate's `resume_with` keys. Status contract: `completed | input-required | failed`.

