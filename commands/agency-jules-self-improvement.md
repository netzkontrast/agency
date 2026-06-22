---
description: Walk the `jules-self-improvement` discipline — `/agency-jules-self-improvement` drives `develop.skill_walk(name='jules-self-improvement')`, delivering ONE phase at a time and recording the SkillRun provenance (Spec 018 Win 1).
---

## `/agency-jules-self-improvement` — walk the `jules-self-improvement` discipline

Phases: collect-dogfood → fold-into-graph

Each phase records a `Phase` node and the SkillRun `SERVES` the active Intent; the engine pauses at hard gates.

| # | Phase | Input | Output | Verbs | Gate |
|---|-------|-------|--------|-------|------|
| 1 | collect-dogfood | plan_dir | collection | — |  |
| 2 | fold-into-graph | scope, texts | reflections | — |  |

```python
await call_tool('capability_develop_skill_walk', {'name': 'jules-self-improvement', 'inputs': {}})
```

Resume after a paused gate with `resume_from='<skill_id>'` and the gate's `resume_with` keys. Status contract: `completed | input-required | failed`.

