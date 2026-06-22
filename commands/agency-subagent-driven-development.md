---
description: Walk the `subagent-driven-development` discipline — `/agency-subagent-driven-development` drives `develop.skill_walk(name='subagent-driven-development')`, delivering ONE phase at a time and recording the SkillRun provenance (Spec 018 Win 1).
---

## `/agency-subagent-driven-development` — walk the `subagent-driven-development` discipline

Phases: write-spec → dispatch → spec-review → code-review

Each phase records a `Phase` node and the SkillRun `SERVES` the active Intent; the engine pauses at hard gates.

| # | Phase | Input | Output | Verbs | Gate |
|---|-------|-------|--------|-------|------|
| 1 | write-spec | — | task_spec | — |  |
| 2 | dispatch | — | implementation | `subagent.develop` |  |
| 3 | spec-review | — | spec_passed | — | soft |
| 4 | code-review | — | quality_passed | — | hard |

```python
await call_tool('capability_develop_skill_walk', {'name': 'subagent-driven-development', 'inputs': {}})
```

Resume after a paused gate with `resume_from='<skill_id>'` and the gate's `resume_with` keys. Status contract: `completed | input-required | failed`.

### Verbs invoked (full params one-deep)

- `subagent.develop` → `skills/subagent/references/develop.md`

