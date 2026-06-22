---
description: Walk the `tdd` discipline — `/agency-tdd` drives `develop.skill_walk(name='tdd')`, delivering ONE phase at a time and recording the SkillRun provenance (Spec 018 Win 1).
---

## `/agency-tdd` — walk the `tdd` discipline

Phases: red → green → refactor → verify

Each phase records a `Phase` node and the SkillRun `SERVES` the active Intent; the engine pauses at hard gates.

| # | Phase | Input | Output | Verbs | Gate |
|---|-------|-------|--------|-------|------|
| 1 | red | — | failing_test | — |  |
| 2 | green | — | implementation | — |  |
| 3 | refactor | — | refactored | — |  |
| 4 | verify | — | tests_pass | — | hard |

```python
await call_tool('capability_develop_skill_walk', {'name': 'tdd', 'inputs': {}})
```

Resume after a paused gate with `resume_from='<skill_id>'` and the gate's `resume_with` keys. Status contract: `completed | input-required | failed`.

