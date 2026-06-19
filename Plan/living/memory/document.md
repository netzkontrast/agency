---
capability: document
pillar: memory
vision_goals: [2, 7, 9]
status: living
last_generated: 2026-06-19
sources: [43, 292]
---

# document — Document renders graph-native briefings: an index of a repo, an explanation of a subsystem, or a markdown rendering produced on demand from the graph (memory pillar)

## Why
<!-- AUTHORED (the only hand-written section). The intent + trade-offs the
     code can't express. A per-pillar subagent fills this from the archived
     specs in sources:. Everything below is GENERATED — do not hand-edit. -->
Document renders graph-native briefings and indices so a repository or subsystem's structure becomes understandable without loading every file, and all rendering is bidirectional — markdown and graph stay in sync as interconnected peers.

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
