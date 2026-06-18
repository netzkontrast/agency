---
description: Walk the `approach-routing` skill — `/agency-approach-routing` drives `develop.skill_walk(name='approach-routing')` so the engine delivers ONE phase at a time and records the SkillRun provenance (Spec 018 Win 1).
---

## `/agency-approach-routing` — walk `approach-routing`

Drive the `approach-routing` skill atomically (Spec 018) so each phase records a `Phase` node + the SkillRun records `SERVES` the active Intent. The engine pauses at hard gates; resume with the gate's `resume_with` keys.

### How

```python
await call_tool('capability_develop_skill_walk', {
    'name': 'approach-routing',
    'inputs': {},
})
```

To resume after a paused gate, pass `resume_from='<skill_id>'` and `inputs={<gate.resume_with keys>}`. The walker returns the typed status contract: `completed | input-required | failed`.

### Derived

This command is auto-generated from the live capability registry by `install.generate()` per Spec 148 Slice 2; deleting it WILL NOT remove the skill, but the next install rewrites the file from the live ontology.

