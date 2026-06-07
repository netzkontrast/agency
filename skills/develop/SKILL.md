<!-- agency-generated: v1 -->
---
name: develop
description: Use when building the system further — walking a development discipline (tdd, plan, review), scaffolding a new capability, or running a skill to its first hard gate.
allowed-tools:
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
  - mcp__plugin_agency_agency__execute
  - Bash
---

# develop capability

Develop owns the development disciplines as walkable skills, a capability scaffolder that lints clean, and an atomic skill walker that records every phase as provenance.

## When to use

- About to implement a feature or fix without a discipline
- A new capability needing a skeleton that lints clean
- A multi-phase workflow that should pause at a human gate

## Verbs

| Verb | Role | Brief | Reference |
|------|------|-------|-----------|
| `checklist` | transform | Project a discipline (skill walk) into a step-by-step checklist. | [details](references/checklist.md) |
| `estimate` | transform | Decidable effort estimate from change-size inputs (Spec 046 F-D — sc-estimate, DECIDABLE only: no LLM, a transparent formula over the inputs you can count). | [details](references/estimate.md) |
| `record_authoring_outcome` | act | Record a Reflection at the end of an authoring-capabilities walk. | [details](references/record_authoring_outcome.md) |
| `reference` | transform | Fetch a discipline's heavy how-to on demand (T3 disclosure). | [details](references/reference.md) |
| `scaffold_capability` | act | Emit a CAPABILITY-AUTHORING.md-compliant capability skeleton. | [details](references/scaffold_capability.md) |
| `skill_walk` | act | Walk a registered skill to the first hard gate in ONE call (the atomic walker). | [details](#skill_walk) |
| `validate_skill` | transform | Validate a capability's Agent-Skill (its SkillDoc) — lint + dry-run emit. | [details](references/validate_skill.md) |

## Example

```bash
await call_tool('capability_develop_checklist', {'intent_id': 'intent:abc'})
```

## Red flags — stop and re-read this skill

- Writing implementation before a failing test → walk capability_develop_skill_walk with tdd
- Hand-rolling a capability skeleton → use capability_develop_scaffold_capability

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
- **`plan`** (discipline): map → self-review → approve
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'plan', 'inputs': {}, 'intent_id': '…'})`
- **`review`** (discipline): request → dispatch → resolve
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'review', 'inputs': {}, 'intent_id': '…'})`
- **`spec-panel`** (discipline): review → synthesize → approve
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'spec-panel', 'inputs': {}, 'intent_id': '…'})`
- **`tdd`** (discipline): red → green → refactor → verify
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'tdd', 'inputs': {}, 'intent_id': '…'})`
- **`verify`** (discipline): identify → run → confirm
  — walk it: `await call_tool('capability_develop_skill_walk', {'name': 'verify', 'inputs': {}, 'intent_id': '…'})`

## skill_walk

Walk a registered skill to the first hard gate in ONE call (the atomic walker).

Parameters: `(name: 'str', inputs: 'dict', resume_from: 'str' = '')`.

_(Tier B — verb docstring lacks Spec 016 Inputs:/Returns:/chain_next: markers; reference is in-skill only. Add markers to upgrade to a separate references/skill_walk.md.)_
