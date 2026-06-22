---
description: Walk the `jules-recovery-when-stuck` discipline — `/agency-jules-recovery-when-stuck` drives `develop.skill_walk(name='jules-recovery-when-stuck')`, delivering ONE phase at a time and recording the SkillRun provenance (Spec 018 Win 1).
---

## `/agency-jules-recovery-when-stuck` — walk the `jules-recovery-when-stuck` discipline

Phases: classify-state → probe-once → patch-or-empty → recovered

Each phase records a `Phase` node and the SkillRun `SERVES` the active Intent; the engine pauses at hard gates.

| # | Phase | Input | Output | Verbs | Gate |
|---|-------|-------|--------|-------|------|
| 1 | classify-state | session | status | — |  |
| 2 | probe-once | session, prompt | probe | — |  |
| 3 | patch-or-empty | session | patch | — |  |
| 4 | recovered | — | pr_url | — | hard |

```python
await call_tool('capability_develop_skill_walk', {'name': 'jules-recovery-when-stuck', 'inputs': {}})
```

Resume after a paused gate with `resume_from='<skill_id>'` and the gate's `resume_with` keys. Status contract: `completed | input-required | failed`.

