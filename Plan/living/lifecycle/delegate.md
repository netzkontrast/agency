---
capability: delegate
pillar: lifecycle
vision_goals: []        # TODO(why-author): which GOALS.md goals this serves
status: living
last_generated: 2026-06-13
sources: []             # TODO(why-author): archived Plan/_archive/NNN specs that built this
---

# delegate — Delegate weighs the token-economics and safety signals of dispatching, fans a task out to one or more drivers, and reduces their results back into a single answer (lifecycle pillar)

## Why
<!-- AUTHORED (the only hand-written section). The intent + trade-offs the
     code can't express. A per-pillar subagent fills this from the archived
     specs in sources:. Everything below is GENERATED — do not hand-edit. -->
_TODO: authored intent._

## Verbs (generated · 4)

| Verb | Role | Params (**required**) | Purpose |
|---|---|---|---|
| `delegate.dispatch_bash_hints` | transform | paths · symbols | Compose the bash-hint context block for a dispatch prompt. |
| `delegate.dispatch_decision` | transform | file_count · exploration_needed · parallelism · est_duration_min · expected_return_tokens · mutates · read_only · driver_hint · context_overlap · cache_warmth · local_budget_relevant | Apply the dispatch-vs-inline heuristic and return a recommendation. |
| `delegate.fan_out` | effect | **driver** · **driver_verb** · **items** · quota | Open one child Lifecycle per item (capped at `quota`), dispatch the driver |
| `delegate.join` | act | **delegation** | Reduce a delegation over its children's Lifecycle state. |

## Ontology (generated)

**Nodes:** `Delegation`(driver, driver_verb, count, quota)
**Edges:** `DELEGATES_TO` · `REDUCES_INTO`

## Skills (generated)

_(no walkable skills)_

<!-- doc-source: agency/capabilities/delegate -->
