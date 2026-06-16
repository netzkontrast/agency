---
spec: 298
title: recommend-routing-capability
status: Partial (Slice 1 shipped)
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
- [ ] **Follow-up:** rank by graph usage frequency; fold into the coverage map.

## Followup — Implementation Status (2026-06-16)

**Done.** `agency/capabilities/recommend/` — `route`; reads the live registry;
`Recommendation` node. **Still.** Usage-frequency ranking.
