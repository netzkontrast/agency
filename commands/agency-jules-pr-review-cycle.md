---
description: Walk the `jules-pr-review-cycle` discipline — `/agency-jules-pr-review-cycle` drives `develop.skill_walk(name='jules-pr-review-cycle')`, delivering ONE phase at a time and recording the SkillRun provenance (Spec 018 Win 1).
---

## `/agency-jules-pr-review-cycle` — walk the `jules-pr-review-cycle` discipline

Phases: read-comments → draft-replies → reply-on-github

Drive the skill atomically — each phase records a `Phase` node and the SkillRun `SERVES` the active Intent; the engine pauses at hard gates.

```python
await call_tool('capability_develop_skill_walk', {'name': 'jules-pr-review-cycle', 'inputs': {}})
```

Resume after a paused gate with `resume_from='<skill_id>'` and the gate's `resume_with` keys. Status contract: `completed | input-required | failed`.

