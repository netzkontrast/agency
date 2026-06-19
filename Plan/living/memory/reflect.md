---
capability: reflect
pillar: memory
vision_goals: [2, 6, 7]
status: living
last_generated: 2026-06-19
sources: [45]
---

# reflect — Reflect is the cross-session memory surface: scope-tagged notes recorded as graph nodes, recalled by scope or by semantic similarity against prior observations (memory pillar)

## Why
<!-- AUTHORED (the only hand-written section). The intent + trade-offs the
     code can't express. A per-pillar subagent fills this from the archived
     specs in sources:. Everything below is GENERATED — do not hand-edit. -->
Reflect is scope-tagged cross-session memory — insights recorded as graph nodes and recalled by scope or semantic similarity — so lessons outlive the session and repeated rediscovery becomes a traced fact rather than an invisible tax.

## Verbs (generated · 6)

| Verb | Role | Params (**required**) | Purpose |
|---|---|---|---|
| `reflect.batch_note` | act | **scope** · **texts** | Bulk version of ``note``: one Reflection node per text. |
| `reflect.note` | act | **scope** · **text** | Write a scope-tagged insight node; edged OBSERVED_DURING + SERVES the intent. |
| `reflect.recall` | transform | scope | Retrieve reflections, newest first, optionally filtered by scope. |
| `reflect.recall_semantic` | transform | **embedder** · **query** · k · scope | Semantic top-k recall over Reflection nodes; backend-injectable. |
| `reflect.search` | transform | **query** | Keyword search over reflection text (deterministic substring match). |
| `reflect.synthesize_session` | act | **session_lifecycle_id** · lessons · open_questions · handoff_notes | Produce a session-reflection artefact at session close (act). |

## Ontology (generated)

**Nodes:** `Reflection`(scope, text)
**Edges:** `INFORMS` · `OBSERVED_DURING`
**Enums:** `('Reflection', 'scope')` ∈ {observation, project, reflection, technical, user, world}

## Skills (generated)

_(no walkable skills)_

<!-- doc-source: agency/capabilities/reflect -->
