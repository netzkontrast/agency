---
description: Walk the `debug` discipline — `/agency-debug` drives `develop.skill_walk(name='debug')`, delivering ONE phase at a time and recording the SkillRun provenance (Spec 018 Win 1).
---

## `/agency-debug` — walk the `debug` discipline

Phases: gather → hypothesize → trace → fix

Each phase records a `Phase` node and the SkillRun `SERVES` the active Intent; the engine pauses at hard gates.

| # | Phase | Input | Output | Verbs | Gate |
|---|-------|-------|--------|-------|------|
| 1 | gather | — | evidence | — |  |
| 2 | hypothesize | — | hypothesis | — |  |
| 3 | trace | — | root_cause | — |  |
| 4 | fix | — | fix_verified | — | hard |

```python
await call_tool('capability_develop_skill_walk', {'name': 'debug', 'inputs': {}})
```

Resume after a paused gate with `resume_from='<skill_id>'` and the gate's `resume_with` keys. Status contract: `completed | input-required | failed`.

