---
capability: gate
pillar: lifecycle
vision_goals: []        # TODO(why-author): which GOALS.md goals this serves
status: living
last_generated: 2026-06-13
sources: []             # TODO(why-author): archived Plan/_archive/NNN specs that built this
---

# gate — Gate evaluates a reusable predicate and records the outcome as a Gate node edged into the lifecycle and intent, so a pass or block is auditable provenance (lifecycle pillar)

## Why
<!-- AUTHORED (the only hand-written section). The intent + trade-offs the
     code can't express. A per-pillar subagent fills this from the archived
     specs in sources:. Everything below is GENERATED — do not hand-edit. -->
_TODO: authored intent._

## Verbs (generated · 1)

| Verb | Role | Params (**required**) | Purpose |
|---|---|---|---|
| `gate.check` | act | **lifecycle_id** · **name** · **passed** · evidence | Record a gate outcome on a Lifecycle: PASSED, or BLOCKED_ON + |

## Ontology (generated)

_(no ontology extension)_

## Skills (generated)

_(no walkable skills)_

<!-- doc-source: agency/capabilities/gate -->
