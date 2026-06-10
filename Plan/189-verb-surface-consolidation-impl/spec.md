---
spec_id: "189"
slug: verb-surface-consolidation-impl
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "070"
depends_on: ["070", "067", "182", "149"]
vision_goals: [1, 4]
affects:
  - agency/capabilities/
  - tests/test_verb_consolidation.py
---

# Spec 189 — verb-surface consolidation implementation

## Why

Spec 070 (verb-surface-consolidation) is WARN-accepted / "optional
future" in the token-economy cluster — the lint flags redundant verbs
but no consolidation shipped. As the enhancement waves add verbs
(AnthropicDriver consumers, judge axes, opportunity detectors), the
surface grows; periodic consolidation keeps discovery cheap (Goal 1).
This spec runs the consolidation the 070 lint recommends, derived from
the live duplicate-verb report.

## Done When

- [ ] **The 070 lint's redundant-verb report drives a consolidation
      pass** — near-duplicate verbs alias-and-deprecate to one
      canonical (never a hard break).
- [ ] **The consolidation is derived** (Spec 149) — the report ranks
      candidates by call-frequency × semantic overlap.
- [ ] **Cluster-coherence (Spec 182) re-checked** post-consolidation.
- [ ] **Discovery token count drops** measurably (rule 8 relationship).
- [ ] Test: a duplicate-verb fixture consolidates; the alias still
      resolves; cluster map stays coherent.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 067 (lint pipeline) supplies the redundancy report.
- Spec 182 (cluster audit) validates the result.
- **Drift-derivation chain** (149).

## Open questions

1. Auto-alias or human-confirm each? **Recommend**: human-confirm v1
   (consolidation is judgement); the report proposes, a person accepts.
