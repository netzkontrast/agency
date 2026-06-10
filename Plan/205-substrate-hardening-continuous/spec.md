---
spec_id: "205"
slug: substrate-hardening-continuous
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "092"
depends_on: ["092", "155", "157", "149"]
vision_goals: [6, 4]
affects:
  - scripts/check-drift
  - tests/test_substrate_hardening_continuous.py
---

# Spec 205 — continuous substrate hardening

## Why

Spec 092 shipped six substrate-hardening fixes (installer prune,
reserved-name lints, OpenRouter Driver, intent→develop cues, doc-drift
in CI, followup-grounding) as a one-time 6-PR wave. Like the red-team
re-runner (Spec 155) generalizes Spec 006, this generalizes 092: the
six fixes become STANDING checks so the substrate can't regress on any
of them — reserved-names stay enforced, doc-drift stays gated,
followup-grounding stays required.

## Done When

- [ ] **Each of the six 092 fixes has a standing check** in
      `check-drift` (Spec 054 family) or CI — a regression on any one
      fails the build.
- [ ] **The followup-grounding rule (G6)** is enforced by the derived-
      doc discipline (Spec 149) — a spec whose Followup cites a
      file:line that no longer exists fails.
- [ ] **The reserved-name lint (G2)** covers the new enhancement-era
      names (AnthropicDriver, etc.).
- [ ] Test: a regression of each 092 fix trips its standing check.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 155 (red-team re-runner) is the parallel generalize-a-one-time-
  pass spec.
- Spec 157 (architecture gate) + Spec 149 (drift) host the checks.

## Open questions

1. All six as hard gates? **Recommend**: yes — they were correctness
   fixes; a regression is a real bug, not a style nit.
