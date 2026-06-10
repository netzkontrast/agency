---
spec_id: "258"
slug: dogfood-classifier-quality-loop
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "150"
depends_on: ["150", "147", "181", "199"]
vision_goals: [6]
affects:
  - agency/capabilities/dogfood/_main.py
  - tests/test_dogfood_quality_loop.py
---

# Spec 258 — dogfood classifier: rubric-eval quality loop

## Why

Spec 150 anchors the dogfood-loop chain — classifier emits amendment
proposals. Proposal QUALITY needs measurement. The `claude-api` skill's
Managed-Agents Outcome surface (gradeable rubric, iterate to satisfied)
is the natural quality engine: the classifier proposes; a rubric checks
"cites ≥1 reflection · names a real spec_id · op valid · rationale
non-empty"; iterations satisfy or fail; the loop measures itself.

## Done When

- [ ] **Optional Managed-Agents Outcome path** — `parse_amendment(...,
      outcome=True)` uses the vendored amendment.rubric.md as a gradeable
      Outcome (claude-api skill).
- [ ] **Quality metric derived** — proposal-accept rate over time
      (Spec 149); regression alarms.
- [ ] **Embedder upgrade (Spec 181) feeds candidate quality.**
- [ ] **Trigger validation via Spec 199** for proposals that propose new
      verbs/skills.
- [ ] Test: outcome iterates a vague proposal to a sharp one (mocked);
      accept-rate derived correctly.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 150 (parent); Spec 181 (recall quality); Spec 199 (trigger valid).
- **Dogfood-loop chain** completion.
