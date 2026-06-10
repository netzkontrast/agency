---
spec_id: "233"
slug: worldbuilding-slice2-impl
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "123"
depends_on: ["123", "138", "147", "150"]
vision_goals: [4]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_worldbuilding_slice2.py
---

# Spec 233 — worldbuilding Slice 2 (Conflict/Theme/PlantedElement)

## Why

Spec 123 ships World sub-graph Slice 1; its Followup names Slice 2:
Conflict + Theme tracking + PlantedElement foreshadowing + skill
rewiring + `developmental_gate` extension. The PsychProfile carve-out
is superseded by Spec 138 (plural-character) — but Conflict/Theme/
PlantedElement remain. Plus an optional Spec 147 judgement pass for
axiom contradictions Open Q2 deferred.

## Done When

- [ ] **Conflict + Theme nodes + 4 verbs** (novel-scoped per Open Q1).
- [ ] **PlantedElement + Chekhov's-gun audit** (the foreshadowing
      surface; complement to Spec 140's named Anchor).
- [ ] **`developmental_gate` extension** chains Conflict/Theme coverage.
- [ ] **Optional judgement pass** via `thinking.red_team` (Spec 147)
      for axiom contradictions (Open Q2 closed).
- [ ] Test: Chekhov audit + theme coverage on a fixture novel.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 138 supersedes PsychProfile; Spec 140 (Anchor) sibling.
- **LLM-driver chain** (147) for the judgement pass.
