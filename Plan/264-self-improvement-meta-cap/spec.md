---
spec_id: "264"
slug: self-improvement-meta-cap
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "150"
depends_on: ["150", "258", "183", "261"]
vision_goals: [6]
affects:
  - agency/capabilities/develop/_main.py
  - tests/test_self_improvement.py
---

# Spec 264 — self-improvement meta-cap (close the loop end-to-end)

## Why

Spec 150 ships the classifier. Spec 258 measures classifier quality.
Spec 183 detects verb opportunities. Spec 261 audits charter closure.
The meta-cap COMPOSES these into ONE driver verb: `develop.self_improve()`
finds the highest-leverage gap, proposes a spec for it, opens a PR
draft. This is what GOALS.md Goal 6 ("doctrine evolves through
dogfooding") actually looks like in operation.

## Done When

- [ ] **`develop.self_improve(window="...")`** runs the cycle: detect
      opportunities (183) + classify reflections (150) + check closure
      (261) → produces one proposed spec amendment + opens a PR draft.
- [ ] **Driver-mediated proposal authoring** via Spec 147 (the spec
      body itself).
- [ ] **Human approves before merge** — never silent canon (137).
- [ ] **The meta-cap is recursively applied** — `self_improve` can
      propose enhancements to itself (the closing of Goal 6).
- [ ] Test: end-to-end cycle on a fixture proposes a sensible amendment.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 150 + 258 + 183 + 261 composed.
- **Dogfood-loop chain** closure.
