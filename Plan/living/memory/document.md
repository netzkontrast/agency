---
capability: document
pillar: memory
vision_goals: []        # TODO(why-author): which GOALS.md goals this serves
status: living
last_generated: 2026-06-13
sources: []             # TODO(why-author): archived Plan/_archive/NNN specs that built this
---

# document — Document renders graph-native briefings: an index of a repo, an explanation of a subsystem, or a markdown rendering produced on demand from the graph (memory pillar)

## Why
<!-- AUTHORED (the only hand-written section). The intent + trade-offs the
     code can't express. A per-pillar subagent fills this from the archived
     specs in sources:. Everything below is GENERATED — do not hand-edit. -->
_TODO: authored intent._

## Verbs (generated · 3)

| Verb | Role | Params (**required**) | Purpose |
|---|---|---|---|
| `document.explain` | act | **target** · depth | Deterministic code → markdown explanation; emits a Reflection. |
| `document.index_repo` | effect | path · apply · max_tokens | 94%-reduction repo briefing — deterministic; ≤ max_tokens. |
| `document.render` | transform | **scope** · for_intent_id · format | Project graph state to markdown; deterministic. |

## Ontology (generated)

**Nodes:** `RepoIndex`(path, content_sha, token_count, generated_at)
**Edges:** `INDEXES`

## Skills (generated)

_(no walkable skills)_

<!-- doc-source: agency/capabilities/document -->
