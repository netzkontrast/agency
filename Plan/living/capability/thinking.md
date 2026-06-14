---
capability: thinking
pillar: capability
vision_goals: []        # TODO(why-author): which GOALS.md goals this serves
status: living
last_generated: 2026-06-13
sources: []             # TODO(why-author): archived Plan/_archive/NNN specs that built this
---

# thinking — 10 method verbs (8 founding + 2 net-new: red_team + socratic) + 1 composite (apply_full_review) + 1 walkable skill (critical-thinking) (capability pillar)

## Why
<!-- AUTHORED (the only hand-written section). The intent + trade-offs the
     code can't express. A per-pillar subagent fills this from the archived
     specs in sources:. Everything below is GENERATED — do not hand-edit. -->
_TODO: authored intent._

## Verbs (generated · 11)

| Verb | Role | Params (**required**) | Purpose |
|---|---|---|---|
| `thinking.apply_full_review` | act | subject · depth | Run the 8 founding methods in sequence; produce thinking-analysis artefact (act). |
| `thinking.assumptions` | transform | subject | Surface + classify implicit assumptions (load-bearing vs not) (transform). |
| `thinking.decompose` | transform | subject | MECE sub-problem decomposition (transform). |
| `thinking.first_principles` | transform | subject | Strip the goal to fundamentals + reconstruct (transform). |
| `thinking.inversion` | transform | subject | Look for what guarantees failure rather than what guarantees success. |
| `thinking.premortem` | transform | subject | Prospective failure analysis (transform). |
| `thinking.red_team` | transform | subject · n_attacks | Adversarial review — adopt an attacker's stance + find failure paths (transform). |
| `thinking.second_order` | transform | subject · n_steps | Trace consequences N steps downstream (transform). |
| `thinking.socratic` | transform | subject · n_questions | Five-whys-deeper Socratic questioning (transform). |
| `thinking.steelman` | transform | subject · position | Build the strongest possible argument against a position (transform). |
| `thinking.tradeoffs` | transform | subject · options · criteria | Multi-criteria option scoring (transform). |

## Ontology (generated)

**Nodes:** `ThinkingMethod`(method, subject) · `ThinkingFinding`(method, subject, severity)
**Edges:** `ANALYZES`
**Enums:** `('ThinkingFinding', 'severity')` ∈ {critical, high, low, medium}

## Skills (generated)

_(no walkable skills)_

<!-- doc-source: agency/capabilities/thinking -->
