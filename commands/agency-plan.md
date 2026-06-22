---
description: Walk the `plan` discipline — `/agency-plan` drives `develop.skill_walk(name='plan')`, delivering ONE phase at a time and recording the SkillRun provenance (Spec 018 Win 1).
---

## `/agency-plan` — walk the `plan` discipline

Phases: map → self-review → approve

Each phase records a `Phase` node and the SkillRun `SERVES` the active Intent; the engine pauses at hard gates.

| # | Phase | Input | Output | Verbs | Gate |
|---|-------|-------|--------|-------|------|
| 1 | map | — | files, steps | `intent.decompose` |  |
| 2 | self-review | — | gaps_checked | `intent.premortem`, `intent.inversion` |  |
| 3 | approve | — | user_confirmed | — | hard |

```python
await call_tool('capability_develop_skill_walk', {'name': 'plan', 'inputs': {}})
```

Resume after a paused gate with `resume_from='<skill_id>'` and the gate's `resume_with` keys. Status contract: `completed | input-required | failed`.

### Verbs invoked (full params one-deep)

- `intent.decompose` → `skills/intent/references/decompose.md`
- `intent.premortem` → `skills/intent/references/premortem.md`
- `intent.inversion` → `skills/intent/references/inversion.md`

