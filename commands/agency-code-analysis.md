---
description: Walk the `code-analysis` discipline — `/agency-code-analysis` drives `develop.skill_walk(name='code-analysis')`, delivering ONE phase at a time and recording the SkillRun provenance (Spec 018 Win 1).
---

## `/agency-code-analysis` — walk the `code-analysis` discipline

Phases: scope → axes → run → review → apply

Drive the skill atomically — each phase records a `Phase` node and the SkillRun `SERVES` the active Intent; the engine pauses at hard gates.

```python
await call_tool('capability_develop_skill_walk', {'name': 'code-analysis', 'inputs': {}})
```

Resume after a paused gate with `resume_from='<skill_id>'` and the gate's `resume_with` keys. Status contract: `completed | input-required | failed`.

