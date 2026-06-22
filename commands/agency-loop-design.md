---
description: Walk the `loop-design` discipline — `/agency-loop-design` drives `develop.skill_walk(name='loop-design')`, delivering ONE phase at a time and recording the SkillRun provenance (Spec 018 Win 1).
---

## `/agency-loop-design` — walk the `loop-design` discipline

Phases: goal → verification → host → council → control → confirm → emit

Each phase records a `Phase` node and the SkillRun `SERVES` the active Intent; the engine pauses at hard gates.

| # | Phase | Input | Output | Verbs | Gate |
|---|-------|-------|--------|-------|------|
| 1 | goal | — | goal_id | `intent.capture`, `intent.confirm` |  |
| 2 | verification | — | criteria | `gate.check` |  |
| 3 | host | — | host | `persona.create` |  |
| 4 | council | — | council | `persona.create`, `panel.convene` | hard |
| 5 | control | — | loop_id | `lifecycle.open` | hard |
| 6 | confirm | — | preview_ok | `_loop.preview` |  |
| 7 | emit | — | emitted | `_loop.emit` |  |

```python
await call_tool('capability_develop_skill_walk', {'name': 'loop-design', 'inputs': {}})
```

Resume after a paused gate with `resume_from='<skill_id>'` and the gate's `resume_with` keys. Status contract: `completed | input-required | failed`.

### Verbs invoked (full params one-deep)

- `intent.capture`
- `intent.confirm`
- `gate.check` → `skills/gate/references/check.md`
- `persona.create`
- `panel.convene` → `skills/panel/references/convene.md`
- `lifecycle.open`
- `_loop.preview`
- `_loop.emit`

