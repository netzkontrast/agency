---
description: Walk the `develop-spec` discipline — `/agency-develop-spec` drives `develop.skill_walk(name='develop-spec')`, delivering ONE phase at a time and recording the SkillRun provenance (Spec 018 Win 1).
---

## `/agency-develop-spec` — walk the `develop-spec` discipline

Phases: intent → triage → brainstorm → research → acceptance → spec → spec-panel → brooks-lint → improve → open → adr-approve → inprogress → build → lint → done

Each phase records a `Phase` node and the SkillRun `SERVES` the active Intent; the engine pauses at hard gates.

| # | Phase | Input | Output | Verbs | Gate |
|---|-------|-------|--------|-------|------|
| 1 | intent | — | intent_id | `intent.capture` |  |
| 2 | triage | — | scope | `discover.interview`, `discover.clarify` |  |
| 3 | brainstorm | — | design | `develop.brainstorm` |  |
| 4 | research | — | prior_art | `research.fetch`, `codegraph_explore` |  |
| 5 | acceptance | — | acceptance | `discover.acceptance` |  |
| 6 | spec | — | spec_md | `develop.write_spec` |  |
| 7 | spec-panel | — | panel_findings | `develop.spec_panel`, `panel.convene` |  |
| 8 | brooks-lint | — | brooks_findings | `intent.brooks_lint` |  |
| 9 | improve | — | design_good | — | hard |
| 10 | open | — | decision_drafts | `workflow.move_spec`, `adr.extract_decisions` |  |
| 11 | adr-approve | — | decisions_approved | `adr.approve` | hard |
| 12 | inprogress | — | hints | `workflow.move_spec`, `adr.hints` |  |
| 13 | build | — | implementation | `develop.tdd`, `develop.plan_execute` |  |
| 14 | lint | — | lint_findings | `develop.review`, `analyze.review` |  |
| 15 | done | — | verified | `develop.verify`, `analyze.review`, `workflow.move_spec` | hard |

```python
await call_tool('capability_develop_skill_walk', {'name': 'develop-spec', 'inputs': {}})
```

Resume after a paused gate with `resume_from='<skill_id>'` and the gate's `resume_with` keys. Status contract: `completed | input-required | failed`.

### Verbs invoked (full params one-deep)

- `intent.capture`
- `discover.interview` → `skills/discover/references/interview.md`
- `discover.clarify` → `skills/discover/references/clarify.md`
- `develop.brainstorm`
- `research.fetch`
- `codegraph_explore`
- `discover.acceptance` → `skills/discover/references/acceptance.md`
- `develop.write_spec`
- `develop.spec_panel`
- `panel.convene` → `skills/panel/references/convene.md`
- `intent.brooks_lint` → `skills/intent/references/brooks_lint.md`
- `workflow.move_spec` → `skills/workflow/references/move_spec.md`
- `adr.extract_decisions` → `skills/adr/references/extract_decisions.md`
- `adr.approve` → `skills/adr/references/approve.md`
- `adr.hints` → `skills/adr/references/hints.md`
- `develop.tdd`
- `develop.plan_execute`
- `develop.review` → `skills/develop/references/review.md`
- `analyze.review` → `skills/analyze/references/review.md`
- `develop.verify`

