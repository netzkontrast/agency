---
description: Walk the `repo-briefing` discipline — `/agency-repo-briefing` drives `develop.skill_walk(name='repo-briefing')`, delivering ONE phase at a time and recording the SkillRun provenance (Spec 018 Win 1).
---

## `/agency-repo-briefing` — walk the `repo-briefing` discipline

Phases: scope → scan → render → publish

Each phase records a `Phase` node and the SkillRun `SERVES` the active Intent; the engine pauses at hard gates.

| # | Phase | Input | Output | Verbs | Gate |
|---|-------|-------|--------|-------|------|
| 1 | scope | — | path, max_tokens | — |  |
| 2 | scan | — | index_id, tokens | — |  |
| 3 | render | — | content | — |  |
| 4 | publish | — | written | — | hard |

```python
await call_tool('capability_develop_skill_walk', {'name': 'repo-briefing', 'inputs': {}})
```

Resume after a paused gate with `resume_from='<skill_id>'` and the gate's `resume_with` keys. Status contract: `completed | input-required | failed`.

