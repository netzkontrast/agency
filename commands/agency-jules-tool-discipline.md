---
description: Walk the `jules-tool-discipline` discipline — `/agency-jules-tool-discipline` drives `develop.skill_walk(name='jules-tool-discipline')`, delivering ONE phase at a time and recording the SkillRun provenance (Spec 018 Win 1).
---

## `/agency-jules-tool-discipline` — walk the `jules-tool-discipline` discipline

Phases: apply-tool-discipline

Each phase records a `Phase` node and the SkillRun `SERVES` the active Intent; the engine pauses at hard gates.

| # | Phase | Input | Output | Verbs | Gate |
|---|-------|-------|--------|-------|------|
| 1 | apply-tool-discipline | text, must_name | lint_result | — |  |

```python
await call_tool('capability_develop_skill_walk', {'name': 'jules-tool-discipline', 'inputs': {}})
```

Resume after a paused gate with `resume_from='<skill_id>'` and the gate's `resume_with` keys. Status contract: `completed | input-required | failed`.

