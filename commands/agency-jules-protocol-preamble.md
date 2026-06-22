---
description: Walk the `jules-protocol-preamble` discipline — `/agency-jules-protocol-preamble` drives `develop.skill_walk(name='jules-protocol-preamble')`, delivering ONE phase at a time and recording the SkillRun provenance (Spec 018 Win 1).
---

## `/agency-jules-protocol-preamble` — walk the `jules-protocol-preamble` discipline

Phases: detect-mode → verify-remote-state → name-canonical-tools → set-scope → dispatched

Each phase records a `Phase` node and the SkillRun `SERVES` the active Intent; the engine pauses at hard gates.

| # | Phase | Input | Output | Verbs | Gate |
|---|-------|-------|--------|-------|------|
| 1 | detect-mode | source | mode_decision | — |  |
| 2 | verify-remote-state | state, branch, remote | verify_result | — |  |
| 3 | name-canonical-tools | text, must_name | lint_result | — |  |
| 4 | set-scope | — | affects_paths, no_create_outside, agency_clone_ro_in_delegate | — |  |
| 5 | dispatched | — | session_id | — | hard |

```python
await call_tool('capability_develop_skill_walk', {'name': 'jules-protocol-preamble', 'inputs': {}})
```

Resume after a paused gate with `resume_from='<skill_id>'` and the gate's `resume_with` keys. Status contract: `completed | input-required | failed`.

