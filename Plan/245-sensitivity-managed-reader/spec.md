---
spec_id: "245"
slug: sensitivity-managed-reader
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "135"
depends_on: ["135", "147", "180", "150"]
vision_goals: [4, 8]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_sensitivity_managed.py
---

# Spec 245 — sensitivity reader: Managed-Agent role

## Why

Spec 135 ships SensitivityFinding + the 4-phase walk (scan → review →
revise → sign-off). Phase 2 (review) is the human reader's slot —
elevating `info` findings. With Spec 147 + Managed-Agents (Spec 180
pattern), the review can dispatch to a sensitivity-reader Agent
configured with a specific lens (cultural, disability, gender etc.) —
output is always `proposal` findings the human confirms.

## Done When

- [ ] **`sensitivity_review_managed(scene_id, lens="...")`** dispatches
      a Managed-Agent session per Spec 180; output = `proposal`
      SensitivityFindings, tagged `judged`.
- [ ] **Human review still required** for elevation past `info` (the
      135 doctrine).
- [ ] **Findings feed dogfood loop** (Spec 150) — recurring patterns
      become amendment proposals (lexicon updates).
- [ ] Test: the dispatch returns scoped findings (mocked session).
- [ ] TODO row + drift clean.

## Interconnects

- Spec 180 (Managed-Agent fan-out) is the dispatch pattern.
- **LLM-driver chain** (147); human-in-loop preserved.
