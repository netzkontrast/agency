---
description: Walk the `loop-design` discipline — `/agency-loop-design` drives `develop.skill_walk(name='loop-design')`, delivering ONE phase at a time and recording the SkillRun provenance (Spec 018 Win 1).
---

## `/agency-loop-design` — walk the `loop-design` discipline

Phases: goal → verification → host → council → control → confirm → emit

Drive the skill atomically — each phase records a `Phase` node and the SkillRun `SERVES` the active Intent; the engine pauses at hard gates.

```python
await call_tool('capability_develop_skill_walk', {'name': 'loop-design', 'inputs': {}})
```

Resume after a paused gate with `resume_from='<skill_id>'` and the gate's `resume_with` keys. Status contract: `completed | input-required | failed`.

