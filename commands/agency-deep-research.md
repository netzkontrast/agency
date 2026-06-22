---
description: Walk the `deep-research` discipline — `/agency-deep-research` drives `develop.skill_walk(name='deep-research')`, delivering ONE phase at a time and recording the SkillRun provenance (Spec 018 Win 1).
---

## `/agency-deep-research` — walk the `deep-research` discipline

Phases: plan → fan-out → verify → publish

Each phase records a `Phase` node and the SkillRun `SERVES` the active Intent; the engine pauses at hard gates.

| # | Phase | Input | Output | Verbs | Gate |
|---|-------|-------|--------|-------|------|
| 1 | plan | — | research_id, specialists | — |  |
| 2 | fan-out | — | citations_recorded | — |  |
| 3 | verify | — | verification_status | — |  |
| 4 | publish | — | published | — | hard |

```python
await call_tool('capability_develop_skill_walk', {'name': 'deep-research', 'inputs': {}})
```

Resume after a paused gate with `resume_from='<skill_id>'` and the gate's `resume_with` keys. Status contract: `completed | input-required | failed`.

