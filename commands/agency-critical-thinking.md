---
description: Walk the `critical-thinking` discipline — `/agency-critical-thinking` drives `develop.skill_walk(name='critical-thinking')`, delivering ONE phase at a time and recording the SkillRun provenance (Spec 018 Win 1).
---

## `/agency-critical-thinking` — walk the `critical-thinking` discipline

Phases: frame → surface → stress-test → weigh → decide

Each phase records a `Phase` node and the SkillRun `SERVES` the active Intent; the engine pauses at hard gates.

| # | Phase | Input | Output | Verbs | Gate |
|---|-------|-------|--------|-------|------|
| 1 | frame | — | problem_statement | `decompose` |  |
| 2 | surface | — | assumptions | `assumptions` |  |
| 3 | stress-test | — | failure_modes | `premortem`, `inversion`, `brooks_lint` |  |
| 4 | weigh | — | tradeoffs | `tradeoffs`, `second_order` |  |
| 5 | decide | — | chosen_approach | — | hard |

```python
await call_tool('capability_develop_skill_walk', {'name': 'critical-thinking', 'inputs': {}})
```

Resume after a paused gate with `resume_from='<skill_id>'` and the gate's `resume_with` keys. Status contract: `completed | input-required | failed`.

### Verbs invoked (full params one-deep)

- `decompose`
- `assumptions`
- `premortem`
- `inversion`
- `brooks_lint`
- `tradeoffs`
- `second_order`

