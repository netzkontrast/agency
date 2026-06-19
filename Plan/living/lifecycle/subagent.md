---
capability: subagent
pillar: lifecycle
vision_goals: [2, 3, 8]
status: living
last_generated: 2026-06-19
sources: [40]
---

# subagent — Subagent composes subagent-driven development: a self-contained task is dispatched into a clean context and its verified result returns to the orchestrator (lifecycle pillar)

## Why
<!-- AUTHORED (the only hand-written section). The intent + trade-offs the
     code can't express. A per-pillar subagent fills this from the archived
     specs in sources:. Everything below is GENERATED — do not hand-edit. -->
Subagent isolates a self-contained task into a dispatched context with a two-stage review gate (spec-fidelity then code-quality) so work stays composable while the orchestrator retains oversight and can recover risky implementations.

## Verbs (generated · 1)

| Verb | Role | Params (**required**) | Purpose |
|---|---|---|---|
| `subagent.develop` | effect | **driver** · **driver_verb** · **item** · **spec_passed** · **quality_passed** · spec_evidence · quality_evidence | Dispatch a worker child via delegate, then gate it spec-review→quality-review; done iff both pass. |

## Ontology (generated)

_(no ontology extension)_

## Skills (generated)

_(no walkable skills)_

<!-- doc-source: agency/capabilities/subagent -->
