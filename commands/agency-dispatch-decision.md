---
description: Walk the `dispatch-decision` discipline — `/agency-dispatch-decision` drives `develop.skill_walk(name='dispatch-decision')`, delivering ONE phase at a time and recording the SkillRun provenance (Spec 018 Win 1).
---

## `/agency-dispatch-decision` — walk the `dispatch-decision` discipline

Phases: estimate-tokens-and-cache → estimate-shape → apply-heuristic → assemble-bash-hints → decide

Each phase records a `Phase` node and the SkillRun `SERVES` the active Intent; the engine pauses at hard gates.

| # | Phase | Input | Output | Verbs | Gate |
|---|-------|-------|--------|-------|------|
| 1 | estimate-tokens-and-cache | — | expected_return_tokens, mutates, read_only, driver_hint, context_overlap, cache_warmth, local_budget_relevant | — |  |
| 2 | estimate-shape | — | file_count, exploration_needed, parallelism, est_duration_min | — |  |
| 3 | apply-heuristic | — | recommendation, driver, rationale, signals_fired | — |  |
| 4 | assemble-bash-hints | — | bash_hints | — |  |
| 5 | decide | — | decision | — | hard |

```python
await call_tool('capability_develop_skill_walk', {'name': 'dispatch-decision', 'inputs': {}})
```

Resume after a paused gate with `resume_from='<skill_id>'` and the gate's `resume_with` keys. Status contract: `completed | input-required | failed`.

