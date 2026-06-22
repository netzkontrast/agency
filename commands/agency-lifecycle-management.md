---
description: Walk the `lifecycle-management` discipline — `/agency-lifecycle-management` drives `develop.skill_walk(name='lifecycle-management')`, delivering ONE phase at a time and recording the SkillRun provenance (Spec 018 Win 1).
---

## `/agency-lifecycle-management` — walk the `lifecycle-management` discipline

Phases: survey → triage → unblock → advance → close → report

Each phase records a `Phase` node and the SkillRun `SERVES` the active Intent; the engine pauses at hard gates.

| # | Phase | Input | Output | Verbs | Gate |
|---|-------|-------|--------|-------|------|
| 1 | survey | — | board_state | — |  |
| 2 | triage | — | blockers | — |  |
| 3 | unblock | — | unblocked_lifecycles | — |  |
| 4 | advance | — | progress_recorded | — |  |
| 5 | close | — | terminal_closed | — |  |
| 6 | report | — | lifecycle_board | — |  |

```python
await call_tool('capability_develop_skill_walk', {'name': 'lifecycle-management', 'inputs': {}})
```

Resume after a paused gate with `resume_from='<skill_id>'` and the gate's `resume_with` keys. Status contract: `completed | input-required | failed`.

