---
description: Walk the `guided-discovery` discipline — `/agency-guided-discovery` drives `develop.skill_walk(name='guided-discovery')`, delivering ONE phase at a time and recording the SkillRun provenance (Spec 018 Win 1).
---

## `/agency-guided-discovery` — walk the `guided-discovery` discipline

Phases: elicit → ground → clarify → frame → examine → scope → decide

Each phase records a `Phase` node and the SkillRun `SERVES` the active Intent; the engine pauses at hard gates.

| # | Phase | Input | Output | Verbs | Gate |
|---|-------|-------|--------|-------|------|
| 1 | elicit | — | draft_intent, elicitation_turns | `interview` |  |
| 2 | ground | — | citations, feasibility_signal | `ground`, `feasibility` |  |
| 3 | clarify | — | ambiguities_resolved | `clarify` |  |
| 4 | frame | — | sharp_intent | `frame` |  |
| 5 | examine | — | thinking_findings | `examine` |  |
| 6 | scope | — | scope_boundaries, acceptance_criteria | `scope`, `acceptance` |  |
| 7 | decide | — | confirmed_intent | `clarity` | computed |

```python
await call_tool('capability_develop_skill_walk', {'name': 'guided-discovery', 'inputs': {}})
```

Resume after a paused gate with `resume_from='<skill_id>'` and the gate's `resume_with` keys. Status contract: `completed | input-required | failed`.

### Verbs invoked (full params one-deep)

- `interview`
- `ground`
- `feasibility`
- `clarify`
- `frame`
- `examine`
- `scope`
- `acceptance`
- `clarity`

