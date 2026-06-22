---
description: Walk the `subagent-driven-development` discipline — `/agency-subagent-driven-development` drives `develop.skill_walk(name='subagent-driven-development')`, delivering ONE phase at a time and recording the SkillRun provenance (Spec 018 Win 1).
---

## `/agency-subagent-driven-development` — walk the `subagent-driven-development` discipline

Phases: write-spec → dispatch → spec-review → code-review

Drive the skill atomically — each phase records a `Phase` node and the SkillRun `SERVES` the active Intent; the engine pauses at hard gates.

```python
await call_tool('capability_develop_skill_walk', {'name': 'subagent-driven-development', 'inputs': {}})
```

Resume after a paused gate with `resume_from='<skill_id>'` and the gate's `resume_with` keys. Status contract: `completed | input-required | failed`.

