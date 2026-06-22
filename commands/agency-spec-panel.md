---
description: Walk the `spec-panel` discipline — `/agency-spec-panel` drives `develop.skill_walk(name='spec-panel')`, delivering ONE phase at a time and recording the SkillRun provenance (Spec 018 Win 1).
---

## `/agency-spec-panel` — walk the `spec-panel` discipline

Phases: review → synthesize → approve

Each phase records a `Phase` node and the SkillRun `SERVES` the active Intent; the engine pauses at hard gates.

| # | Phase | Input | Output | Verbs | Gate |
|---|-------|-------|--------|-------|------|
| 1 | review | — | expert_findings | `intent.steelman`, `intent.assumptions`, `intent.premortem` |  |
| 2 | synthesize | — | revised_spec | `intent.tradeoffs` |  |
| 3 | approve | — | user_confirmed | — | hard |

```python
await call_tool('capability_develop_skill_walk', {'name': 'spec-panel', 'inputs': {}})
```

Resume after a paused gate with `resume_from='<skill_id>'` and the gate's `resume_with` keys. Status contract: `completed | input-required | failed`.

### Verbs invoked (full params one-deep)

- `intent.steelman` → `skills/intent/references/steelman.md`
- `intent.assumptions` → `skills/intent/references/assumptions.md`
- `intent.premortem` → `skills/intent/references/premortem.md`
- `intent.tradeoffs` → `skills/intent/references/tradeoffs.md`

