---
capability: skills
pillar: capability
vision_goals: []        # TODO(why-author): which GOALS.md goals this serves
status: living
last_generated: 2026-06-13
sources: []             # TODO(why-author): archived Plan/_archive/NNN specs that built this
---

# skills — Skills makes the skill surface itself a capability: one home to find, render, and lint the phase-graph skills each capability ships on its ontology, instead of reaching them only through the merged ontology dict or the walker (capability pillar)

## Why
<!-- AUTHORED (the only hand-written section). The intent + trade-offs the
     code can't express. A per-pillar subagent fills this from the archived
     specs in sources:. Everything below is GENERATED — do not hand-edit. -->
_TODO: authored intent._

## Verbs (generated · 5)

| Verb | Role | Params (**required**) | Purpose |
|---|---|---|---|
| `skills.find` | transform | kind · capability | Enumerate the walkable skills across all capabilities, with light filters. |
| `skills.index` | effect |  | Promote walkable skills into the graph as Skill + Phase nodes (Spec 026). |
| `skills.lint` | transform | **skill_name** | Validate a skill's phase-graph shape — the structural contract a walk relies on. |
| `skills.rank` | transform | query | Rank walkable skills against a free-text query (Spec 161 Slice 1). |
| `skills.render` | transform | **skill_name** · depth · phase_index | Render one skill to markdown at a chosen depth (progressive disclosure). |

## Ontology (generated)

_(no ontology extension)_

## Skills (generated)

_(no walkable skills)_

<!-- doc-source: agency/capabilities/skills -->
