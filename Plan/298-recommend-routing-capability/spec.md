---
spec: 298
title: recommend-routing-capability
status: Shipped
depends_on: [294, 297]
clusters: [develop, analyze]
vision_goals: [1, 4]
---

# Spec 298 — `recommend`: request → capability routing, first-class

> Fifth extract→spec→reimplement slice (binding goal: all of SuperClaude
> first-class).

SuperClaude's `sc-recommend` recommends the best command for a request.
Reimplemented natively: route a free-text request to the most suitable agency
capability + verb by reading the **live registry** (a core agency feature) and
scoring decidable token overlap. Distinct from `search` (keyword tool lookup):
it routes an intent to a recommended call + rationale, recorded as provenance.

## Design

- `recommend.route(request, top)` — score every live capability by token overlap
  (capability name + verb names + skill names + gist); suggest the
  best-name-matching verb per capability; record a `Recommendation` node
  SERVING the intent.

## Done-When

- [x] `route` reads the live registry + recommends capability+verb with a why.
- [x] `Recommendation` node; provenance; auto-registers; scenarios green.
- [x] **Follow-up:** rank by graph usage frequency.

## Followup — Implementation Status (2026-06-17)

**Done.** `agency/capabilities/recommend/` — `route`; reads the live registry;
`Recommendation` node. **Usage-frequency ranking shipped (2026-06-17):**
`_usage_counts()` tallies per-capability `Invocation` nodes from the provenance
graph; `route` now emits a `usage` field per recommendation and sorts by
`(-score, -usage, capability)` — relevance primary, graph usage frequency breaks
ties (more-used capability wins among equal matches), name is the deterministic
final tie-break. A live signal read from the graph, not a static weight (rule 8).
+1 acceptance scenario (usage reflects two invocations).

**Status: Shipped.** The residual "fold into the coverage map" note is a
cross-spec doc nicety, not capability behaviour.
