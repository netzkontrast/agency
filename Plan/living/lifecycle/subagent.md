---
capability: subagent
pillar: lifecycle
vision_goals: []        # TODO(why-author): which GOALS.md goals this serves
status: living
last_generated: 2026-06-13
sources: []             # TODO(why-author): archived Plan/_archive/NNN specs that built this
---

# subagent — Subagent composes subagent-driven development: a self-contained task is dispatched into a clean context and its verified result returns to the orchestrator (lifecycle pillar)

## Why
<!-- AUTHORED (the only hand-written section). The intent + trade-offs the
     code can't express. A per-pillar subagent fills this from the archived
     specs in sources:. Everything below is GENERATED — do not hand-edit. -->
_TODO: authored intent._

## Verbs (generated · 1)

| Verb | Role | Params (**required**) | Purpose |
|---|---|---|---|
| `subagent.develop` | effect | **driver** · **driver_verb** · **item** · **spec_passed** · **quality_passed** · spec_evidence · quality_evidence | Dispatch a worker child via delegate, then gate it spec-review→quality-review; done iff both pass. |

## Ontology (generated)

_(no ontology extension)_

## Skills (generated)

_(no walkable skills)_

<!-- doc-source: agency/capabilities/subagent -->
