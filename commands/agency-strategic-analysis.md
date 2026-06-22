---
description: Walk the `strategic-analysis` discipline — `/agency-strategic-analysis` drives `develop.skill_walk(name='strategic-analysis')`, delivering ONE phase at a time and recording the SkillRun provenance (Spec 018 Win 1).
---

## `/agency-strategic-analysis` — walk the `strategic-analysis` discipline

Phases: frame → convene → challenge → synthesize

Each phase records a `Phase` node and the SkillRun `SERVES` the active Intent; the engine pauses at hard gates.

| # | Phase | Input | Output | Verbs | Gate |
|---|-------|-------|--------|-------|------|
| 1 | frame | — | subject, mode | — |  |
| 2 | convene | — | experts, analysis | — |  |
| 3 | challenge | — | tensions | — |  |
| 4 | synthesize | — | synthesis | — | hard |

```python
await call_tool('capability_develop_skill_walk', {'name': 'strategic-analysis', 'inputs': {}})
```

Resume after a paused gate with `resume_from='<skill_id>'` and the gate's `resume_with` keys. Status contract: `completed | input-required | failed`.

