---
description: Walk the `guided-discovery` discipline — `/agency-guided-discovery` drives `develop.skill_walk(name='guided-discovery')`, delivering ONE phase at a time and recording the SkillRun provenance (Spec 018 Win 1).
---

## `/agency-guided-discovery` — walk the `guided-discovery` discipline

Phases: elicit → ground → clarify → frame → examine → scope → decide

Drive the skill atomically — each phase records a `Phase` node and the SkillRun `SERVES` the active Intent; the engine pauses at hard gates.

```python
await call_tool('capability_develop_skill_walk', {'name': 'guided-discovery', 'inputs': {}})
```

Resume after a paused gate with `resume_from='<skill_id>'` and the gate's `resume_with` keys. Status contract: `completed | input-required | failed`.

