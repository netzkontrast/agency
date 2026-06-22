---
description: Walk the `mode-selection` discipline — `/agency-mode-selection` drives `develop.skill_walk(name='mode-selection')`, delivering ONE phase at a time and recording the SkillRun provenance (Spec 018 Win 1).
---

## `/agency-mode-selection` — walk the `mode-selection` discipline

Phases: assess → detect → activate → confirm

Drive the skill atomically — each phase records a `Phase` node and the SkillRun `SERVES` the active Intent; the engine pauses at hard gates.

```python
await call_tool('capability_develop_skill_walk', {'name': 'mode-selection', 'inputs': {}})
```

Resume after a paused gate with `resume_from='<skill_id>'` and the gate's `resume_with` keys. Status contract: `completed | input-required | failed`.

