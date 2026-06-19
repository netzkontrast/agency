---
capability: dogfood
pillar: memory
vision_goals: [2, 6, 7, 9]
status: living
last_generated: 2026-06-19
sources: [17, 150]
---

# dogfood — Dogfood keeps observation ledgers graph-native: notes recorded as nodes, exported and imported as JSON preserving ids and validity windows, and rendered to markdown on demand (memory pillar)

## Why
<!-- AUTHORED (the only hand-written section). The intent + trade-offs the
     code can't express. A per-pillar subagent fills this from the archived
     specs in sources:. Everything below is GENERATED — do not hand-edit. -->
Dogfood keeps observation ledgers graph-native with JSON import/export and on-demand markdown rendering, and mechanizes the amendment path so reflections fold back into specs as provenance artefacts, closing the self-improvement loop.

## Verbs (generated · 11)

| Verb | Role | Params (**required**) | Purpose |
|---|---|---|---|
| `dogfood.apply_amendment` | effect | **payload** · dry_run · confirm_token | Render a ProposalPayload as a unified diff; provenance Artefact. |
| `dogfood.boundary_use_audit` | transform | for_intent_id · session_lifecycle_id | Audit BoundaryUse nodes — flag raw-tool uses where a verb exists (transform). |
| `dogfood.collect` | transform | plan_dir | Walk ``plan_dir`` for ``DOGFOOD-NOTES.md`` files; extract observations. |
| `dogfood.export` | effect | path | Dump the provenance store to a portable JSON file. |
| `dogfood.import` | effect | **path** | Replay a JSON export into this graph, preserving ids + windows. |
| `dogfood.note` | act | **observation** · **plan_slug** | Record an observation Reflection tagged with plan_slug. |
| `dogfood.parse_amendment` | transform | scope · since · limit · use_llm · prefer_delegate · host_completion | Classify recent Reflections into amendment proposals. |
| `dogfood.recall_overflow_slice` | transform | body · slice · grep · offset · byte_offset · max_tokens | Spec 154 Slice 3 — recall a paged view of a captured overflow body. |
| `dogfood.record_decision` | effect | **subject** · **decision** · rationale · next_action · session_lifecycle_id | Bind a decision to the current session (effect). |
| `dogfood.render` | transform | **plan_slug** · max_tokens | Project plan_slug observations into DOGFOOD-NOTES.md. |
| `dogfood.replay_events` | transform | for_intent_id · tool · limit | Replay every Event recorded OBSERVED_DURING the given intent |

## Ontology (generated)

**Nodes:** `DecisionRecord`(subject, decision, rationale) · `BoundaryUse`(tool, argument_summary) · `Artefact`(kind)
**Edges:** `PRODUCES_FROM` · `RECORDED_BY` · `RELATES_TO`

## Skills (generated)

_(no walkable skills)_

<!-- doc-source: agency/capabilities/dogfood -->
