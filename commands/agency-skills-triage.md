---
description: Walk the `skills-triage` discipline — `/agency-skills-triage` drives `develop.skill_walk(name='skills-triage')`, delivering ONE phase at a time and recording the SkillRun provenance (Spec 018 Win 1).
---

## `/agency-skills-triage` — walk the `skills-triage` discipline

Phases: enumerate → read → validate → decide

Each phase records a `Phase` node and the SkillRun `SERVES` the active Intent; the engine pauses at hard gates.

| # | Phase | Input | Output | Verbs | Gate |
|---|-------|-------|--------|-------|------|
| 1 | enumerate | — | skill_inventory | `find` |  |
| 2 | read | — | phase_graph | `render` |  |
| 3 | validate | — | lint_report | `lint` | soft |
| 4 | decide | — | chosen_skill | — | hard |

```python
await call_tool('capability_develop_skill_walk', {'name': 'skills-triage', 'inputs': {}})
```

Resume after a paused gate with `resume_from='<skill_id>'` and the gate's `resume_with` keys. Status contract: `completed | input-required | failed`.

### Verbs invoked (full params one-deep)

- `find`
- `render`
- `lint`

