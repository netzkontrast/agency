---
description: Walk the `brainstorm` discipline — `/agency-brainstorm` drives `develop.skill_walk(name='brainstorm')`, delivering ONE phase at a time and recording the SkillRun provenance (Spec 018 Win 1).
---

## `/agency-brainstorm` — walk the `brainstorm` discipline

Phases: explore → present → confirm

Each phase records a `Phase` node and the SkillRun `SERVES` the active Intent; the engine pauses at hard gates.

| # | Phase | Input | Output | Verbs | Gate |
|---|-------|-------|--------|-------|------|
| 1 | explore | — | questions, assumptions | `intent.decompose`, `intent.assumptions`, `intent.first_principles` |  |
| 2 | present | — | design, tradeoffs | `intent.tradeoffs`, `intent.steelman`, `intent.second_order` |  |
| 3 | confirm | — | user_confirmed | — | hard |

```python
await call_tool('capability_develop_skill_walk', {'name': 'brainstorm', 'inputs': {}})
```

Resume after a paused gate with `resume_from='<skill_id>'` and the gate's `resume_with` keys. Status contract: `completed | input-required | failed`.

### Verbs invoked (full params one-deep)

- `intent.decompose` → `skills/intent/references/decompose.md`
- `intent.assumptions` → `skills/intent/references/assumptions.md`
- `intent.first_principles` → `skills/intent/references/first_principles.md`
- `intent.tradeoffs` → `skills/intent/references/tradeoffs.md`
- `intent.steelman` → `skills/intent/references/steelman.md`
- `intent.second_order` → `skills/intent/references/second_order.md`

