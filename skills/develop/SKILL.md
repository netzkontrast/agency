---
name: develop
description: "Use when building the system further — walking a development discipline (tdd, plan, review), scaffolding a new capability, running a skill to its first hard gate, reloading edited capability code mid-session, or looking up code (use codegraph)."
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---
<!-- agency-generated: v1 -->

# develop capability

Develop owns the development disciplines as walkable skills, a capability scaffolder that lints clean, and an atomic skill walker that records every phase as provenance. For ANY code lookup — where/how a symbol works, a call path X→Y, blast radius — reach for codegraph FIRST (`codegraph explore "<q>"` is the one-call primary: relevant source + call paths + impact; `codegraph node <sym|file>` for one symbol's source + caller/callee trail; `codegraph query <name>` to locate) BEFORE grep/Read — it IS the index, so a grep/Read sweep re-does its work. Full token-efficient guide: `develop.reference("codegraph")`.

## When to use

- About to implement a feature or fix without a discipline
- A new capability needing a skeleton that lints clean
- A multi-phase workflow that should pause at a human gate
- A capability was just edited or scaffolded and needs to go live without a restart
- A 'where/how does X work', call-path, or blast-radius question → `codegraph explore "<q>"` (one call), not a grep/Read sweep

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `checklist` | transform | Project a discipline (skill walk) into a step-by-step checklist. | [details](references/checklist.md) |
| `draft_plan` | act | Author a bite-sized plan as graph provenance (Spec 287; rule 2). | [details](references/draft_plan.md) |
| `estimate` | transform | Decidable effort estimate from change-size inputs (Spec 046 F-D — sc-estimate, DECIDABLE only: no LLM, a transparent formula over the inputs you can count). | [details](references/estimate.md) |
| `index` | effect | Index a repo as a token-cheap briefing — the development-workflow entry to the indexer (Spec 292). | [details](references/index.md) |
| `maintain` | act | Drive — and AUTOLEARN — the recurring "Agency Steward" maintenance loop. | [details](references/maintain.md) |
| `mode_select` | effect | Switch session mode + record a ModeShift node (effect). | [details](references/mode_select.md) |
| `optimize_skilldoc` | act | Author an optimized functional doc — flags + candidate, NO rewrite (act). | [details](references/optimize_skilldoc.md) |
| `plan_status` | transform | Roll up a Plan's steps + completion (Spec 287) — the render-on-demand read side (rule 2). | [details](references/plan_status.md) |
| `record_authoring_outcome` | act | Record a Reflection at the end of an authoring-capabilities walk. | [details](references/record_authoring_outcome.md) |
| `record_step_outcome` | act | Mark a PlanStep's execution outcome (Spec 287). | [details](references/record_step_outcome.md) |
| `reference` | transform | Fetch a discipline's heavy how-to on demand (T3 disclosure). | [details](references/reference.md) |
| `reload` | effect | Reload edited capability code into the live session (effect). | [details](references/reload.md) |
| `remediate` | effect | Apply the remedy phase of a prior review — safe fixes auto-applied, risky ones reported as gated (MUTATES → role=effect). | [details](references/remediate.md) |
| `review` | transform | Diagnose code decay using the brooks Iron Law — READ-ONLY (transform). | [details](references/review.md) |
| `scaffold_capability` | act | Emit a CAPABILITY-AUTHORING.md-compliant capability skeleton. | [details](references/scaffold_capability.md) |
| `session_check` | transform | Read the current SessionLifecycle state (transform). | [details](references/session_check.md) |
| `session_init` | act | Mint a SessionLifecycle SERVING the intent, detect mode, and suggest the first verb. | [details](references/session_init.md) |
| `session_resume` | transform | Spec 114 Slice 2 — cross-session handoff. | [details](references/session_resume.md) |
| `skill_walk` | act | Walk a registered skill to the first hard gate in ONE call (the atomic walker). | [details](references/skill_walk.md) |
| `validate_skill` | transform | Validate a capability's Agent-Skill (its SkillDoc) — lint + dry-run emit. | [details](references/validate_skill.md) |

## Example

```bash
await call_tool('capability_develop_checklist', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- Writing implementation before a failing test → walk capability_develop_skill_walk with tdd
- Hand-rolling a capability skeleton → use capability_develop_scaffold_capability
- Restarting the session to pick up a capability edit → develop.reload re-imports it in place
- grep/Read loop to understand code while `.codegraph/` exists → `codegraph explore` already indexed it (`develop.reference("codegraph")`)

## Walk this capability

Drive this capability's verbs by WALKING a skill one phase at a time (progressive disclosure, recorded as provenance):

- **`authoring-capabilities`** (authoring): research → scaffold → author → lint → token-check → commit
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'authoring-capabilities', 'inputs': {}, 'intent_id': '…'})`
- **`brainstorm`** (discipline): explore → present → confirm
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'brainstorm', 'inputs': {}, 'intent_id': '…'})`
- **`debug`** (discipline): gather → hypothesize → trace → fix
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'debug', 'inputs': {}, 'intent_id': '…'})`
- **`execute`** (discipline): load → execute → checkpoint → verify
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'execute', 'inputs': {}, 'intent_id': '…'})`
- **`loop-design`** (discipline): goal → verification → host → council → control → confirm → emit
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'loop-design', 'inputs': {}, 'intent_id': '…'})`
- **`plan`** (discipline): map → self-review → approve
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'plan', 'inputs': {}, 'intent_id': '…'})`
- **`plan-execute`** (discipline): frame → draft-plan → plan-signoff → execute-step → checkpoint → synthesize
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'plan-execute', 'inputs': {}, 'intent_id': '…'})`
- **`quality-audit`** (discipline): scope → decidable → judgment → score-report
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'quality-audit', 'inputs': {}, 'intent_id': '…'})`
- **`quality-debt`** (discipline): scope → decidable → judgment → score-report
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'quality-debt', 'inputs': {}, 'intent_id': '…'})`
- **`quality-health`** (discipline): scope → decidable → judgment → score-report
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'quality-health', 'inputs': {}, 'intent_id': '…'})`
- **`quality-review`** (discipline): scope → decidable → judgment → score-report
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'quality-review', 'inputs': {}, 'intent_id': '…'})`
- **`quality-sweep`** (discipline): scope → decidable → judgment → score-report → remedy
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'quality-sweep', 'inputs': {}, 'intent_id': '…'})`
- **`quality-test`** (discipline): scope → decidable → judgment → score-report
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'quality-test', 'inputs': {}, 'intent_id': '…'})`
- **`review`** (discipline): request → dispatch → resolve
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'review', 'inputs': {}, 'intent_id': '…'})`
- **`session-driver-pass`** (workflow): init → mode-select → work-loop → synthesize → archive
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'session-driver-pass', 'inputs': {}, 'intent_id': '…'})`
- **`spec-panel`** (discipline): review → synthesize → approve
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'spec-panel', 'inputs': {}, 'intent_id': '…'})`
- **`tdd`** (discipline): red → green → refactor → verify
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'tdd', 'inputs': {}, 'intent_id': '…'})`
- **`verify`** (discipline): identify → run → confirm
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'verify', 'inputs': {}, 'intent_id': '…'})`
