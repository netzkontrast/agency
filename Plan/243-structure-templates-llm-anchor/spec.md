---
spec_id: "243"
slug: structure-templates-llm-anchor
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "133"
depends_on: ["133", "147", "217", "150"]
vision_goals: [4, 1]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_structure_llm_anchor.py
---

# Spec 243 — story-structure LLM anchoring

## Why

Spec 133 ships 5 vendored templates (Save the Cat / Three-Act / Hero's
Journey / Story Circle / Snowflake) + `apply_structure` + `anchor_beat`
+ `check_structure_coverage` (flags `|actual-target| > 0.10`). Anchoring
each beat to a chapter is currently manual. With Spec 147, the Driver
can SUGGEST anchors for unanchored beats by matching beat descriptions
against chapter summaries — author confirms, never auto-anchors.

## Done When

- [ ] **`suggest_beat_anchors(novel_id, template_id)`** drives the
      Driver to propose `{beat → chapter}` mappings; `output_config.format`.
- [ ] **Proposals as `proposal` status** (Spec 137); author confirms.
- [ ] **Coverage check (Spec 133) re-runs after each anchor.**
- [ ] **`build-novel` (Spec 217) chains it** as an optional phase.
- [ ] Test: a fixture novel + template yields anchors that pass coverage.
- [ ] TODO row + drift clean.

## Interconnects

- **LLM-driver chain** (147) · **Dogfood-loop** (150).
- Spec 217 (build walkable) chains it.
