---
spec_id: "169"
slug: ci-coverage-and-flake-gate
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "053"
depends_on: ["053", "054", "149", "157"]
vision_goals: [6, 4]
affects:
  - .github/workflows/test.yml
  - scripts/test-coverage-gate
  - tests/test_ci_coverage_gate.py
---

# Spec 169 — CI coverage + flake gate

## Why

Spec 053 ships pytest-xdist + slicing + the CI workflow, but there is
no per-capability COVERAGE floor and no flake detection. The drop-in
bar (CLAUDE.md) says adding a capability should give "a complete,
discoverable, walkable, CLI-exposed, MCP-wired, emittable capability" —
coverage is the missing guarantee. A capability-test-gap report exists
(Spec 054) but doesn't gate.

## Done When

- [ ] **Per-capability coverage floor** — `scripts/test-coverage-gate`
      fails when a capability's line coverage drops below a derived
      baseline (rule 8 — relative, not a pinned %).
- [ ] **Flake detection** — the CI re-runs the changed slice twice;
      a test that passes-then-fails is flagged (not auto-retried-green).
- [ ] **The capability-test-gap report (Spec 054) becomes a GATE** —
      a new verb with zero tests fails CI.
- [ ] Test: a verb with no test trips the gap gate; a coverage drop
      trips the floor.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 054 (drift) supplies the test-gap report.
- Spec 157 (architecture gate) is the sibling standing-gate.
- **Drift-derivation chain** (149): coverage baseline derived.

## Open questions

1. Hard coverage floor or trend-only? **Recommend**: trend (no
   regression) — absolute floors gate fixed solutions (rule 8).
