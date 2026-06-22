---
description: Walk the `execute` discipline — `/agency-execute` drives `develop.skill_walk(name='execute')`, delivering ONE phase at a time and recording the SkillRun provenance (Spec 018 Win 1).
---

## `/agency-execute` — walk the `execute` discipline

Phases: load → execute → checkpoint → verify

Each phase records a `Phase` node and the SkillRun `SERVES` the active Intent; the engine pauses at hard gates.

| # | Phase | Input | Output | Verbs | Gate |
|---|-------|-------|--------|-------|------|
| 1 | load | — | plan, steps | — |  |
| 2 | execute | — | step_results | — |  |
| 3 | checkpoint | — | reviewed | — | hard |
| 4 | verify | — | all_pass | — | hard |

```python
await call_tool('capability_develop_skill_walk', {'name': 'execute', 'inputs': {}})
```

Resume after a paused gate with `resume_from='<skill_id>'` and the gate's `resume_with` keys. Status contract: `completed | input-required | failed`.

