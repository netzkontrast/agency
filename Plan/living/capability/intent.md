---
capability: intent
pillar: capability
vision_goals: []        # TODO(why-author): which GOALS.md goals this serves
status: living
last_generated: 2026-06-13
sources: []             # TODO(why-author): archived Plan/_archive/NNN specs that built this
---

# intent — Intent is the reasoning capability: it turns the human-owned goal into structured critical-thinking scaffolds — decomposition, assumption-surfacing, premortem, first-principles, inversion, steelman, second-order, and trade-off analysis — each a deterministic method an agent fills in against the current intent (capability pillar)

## Why
<!-- AUTHORED (the only hand-written section). The intent + trade-offs the
     code can't express. A per-pillar subagent fills this from the archived
     specs in sources:. Everything below is GENERATED — do not hand-edit. -->
_TODO: authored intent._

## Verbs (generated · 9)

| Verb | Role | Params (**required**) | Purpose |
|---|---|---|---|
| `intent.assumptions` | transform | subject | Surface + classify the implicit assumptions a goal rests on (load-bearing vs not). |
| `intent.decompose` | transform | subject | Decompose a goal into MECE sub-problems — the structured break-down method. |
| `intent.first_principles` | transform | subject | Strip a goal to fundamental truths and rebuild — bypassing inherited assumptions. |
| `intent.inversion` | transform | subject | Invert the goal — ask what would GUARANTEE failure, then avoid exactly that. |
| `intent.premortem` | transform | subject | Premortem — assume the goal FAILED, reason backward to causes + mitigations. |
| `intent.second_order` | transform | subject | Trace second- and third-order consequences — 'and then what?' past the first effect. |
| `intent.steelman` | transform | subject | Build the STRONGEST version of the opposing or alternative position. |
| `intent.suggests` | transform | called_capability · called_verb · called_state · floor | Project the serving intent + the last verb's state to the next applicable |
| `intent.tradeoffs` | transform | options · criteria | Build an explicit trade-off matrix — options × criteria — for a decision. |

## Ontology (generated)

_(no ontology extension)_

## Skills (generated)

_(no walkable skills)_

<!-- doc-source: agency/capabilities/intent -->
