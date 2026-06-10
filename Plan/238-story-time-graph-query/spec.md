---
spec_id: "238"
slug: story-time-graph-query
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "128"
depends_on: ["128", "203", "131", "235"]
vision_goals: [2]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_story_time_query.py
---

# Spec 238 — story-time graph query

## Why

Spec 128 ships StoryTimeEvent + NarrativeBeat + 6 verbs. Many
continuity questions are RELATIONAL ("every event the POV witnessed
before chapter 12", "events HAPPENS_AT a time the antagonist was
elsewhere") — exactly what Spec 203 + Spec 235 typed-paths serve. This
wires story-time onto the moat-query surface.

## Done When

- [ ] **Story-time queries via `analyze.graph_query`** (Spec 203) —
      multi-hop through HAPPENS_AT / REVEALED_IN / PRECEDES.
- [ ] **`narrative_order` derived as typed path** (Spec 235) instead of
      ad-hoc lex sort.
- [ ] **POV knowledge intersection** (Spec 131) composable in one query.
- [ ] Test: cross-event relational queries return expected subgraph.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 203 (graph query) · Spec 235 (typed paths).
- Spec 131 (character knowledge) for POV intersection.
