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

## Done When (measurable invariants — rule 8)

- [ ] **Typed gate result: `GateResult{capability, baseline_coverage:
      float, current_coverage: float, delta: float, flake_count: int,
      missing_tests: list[verb_id], verdict: Literal["pass", "fail"]}`** —
      uniform across the gate's three checks.
- [ ] **Invariant: coverage trend is non-decreasing per capability** —
      `current_coverage >= baseline_coverage - ε`; baseline derives
      from the prior green build, never a pinned %.
- [ ] **Invariant: every live verb has ≥ 1 test** — `set(missing_tests)
      == ∅` for the live registry (Spec 054 test-gap report becomes
      gate). A new verb without a test fails CI.
- [ ] **Invariant: flake detection re-runs the slice TWICE** — a test
      that flips PASS→FAIL→PASS across the two runs registers as
      `flake_count++`; never auto-retried-green.
- [ ] **Relationship: gate verdict == fail iff (delta < -ε OR
      missing_tests ≠ ∅ OR flake_count > 0)** — relationship, not a
      pinned threshold per criterion.
- [ ] **Invariant: baseline storage is the prior green build's
      coverage** — derived (graph node BaselineSnapshot), never
      hand-edited; Spec 149 drift gate catches manual edits.
- [ ] **Failure mode (CI infra):** when the coverage tool itself
      crashes (pytest-cov exception, xdist worker timeout), the gate
      records `verdict=fail` + emits `Codes.GATE_INFRA_ERROR` — never
      silently passes on infra failure.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  capability `analyze` baseline coverage 87%; a PR adds a new
        verb analyze.architecture without tests + drops existing
        coverage to 84%
When:   `scripts/test-coverage-gate analyze` runs in CI
Then:   GateResult{baseline=0.87, current=0.84, delta=-0.03,
        missing_tests=["analyze.architecture"], flake_count=0,
        verdict="fail"}; CI fails with TWO findings (drop + gap)

Given:  same PR adds the test + brings coverage to 87.2%
When:   gate re-runs
Then:   verdict="pass"; baseline updates to 0.872 on merge to main
        (derived, no hand-edit)

Given:  test `test_analyze_architecture::test_cycle_detection`
        passes on run 1, fails on run 2 (timing-dependent), passes
        on rerun
When:   gate runs (two slice runs in CI)
Then:   flake_count=1; verdict="fail"; CI surfaces the flaky test
        name + the seed for repro (never auto-retried-green)
```

## Failure modes

| Failure | Gate response |
|---|---|
| Coverage tool crashes | `GATE_INFRA_ERROR` + fail; never silent pass |
| Flake on the gate itself (test-coverage-gate flaky) | Spec 157 sibling gate catches; rerun under bisect |
| Baseline drift (manual edit of BaselineSnapshot node) | Spec 149 drift fail |
| New capability with 0 verbs (scaffold-only) | gate passes (no verbs to test); doctor flags scaffold |
| Test marked `@pytest.mark.flaky` (auto-retry) | gate refuses to count it as pass; flake_count++ regardless |

## Interconnects

- Spec 054 (drift) supplies the test-gap report this gates on.
- Spec 053 (xdist + slicing) is the runtime substrate.
- Spec 157 (architecture gate) is the sibling standing-gate; both
  consume from analyze axes (Spec 166/167).
- Spec 167 (networkx) — coverage gate protects against non-deterministic
  graph build by re-run.
- Spec 170 (doctor) reports `coverage.live` per capability (derived).
- **Drift-derivation chain** (149): baseline derived per merge, never
  pinned.
- Spec 151 (Codes coverage) supplies `GATE_INFRA_ERROR`.
- Spec 172 (analyzer registry expansion proof) shares the
  property-test pattern.

## Open questions

1. Hard coverage floor or trend-only? **Recommend**: trend (no
   regression with ε buffer) — absolute floors gate fixed solutions
   (rule 8).
2. Slice re-run cadence — every PR or only on suspicion? **Recommend**:
   every PR for the changed slice (Spec 053 keeps it cheap); the full
   suite re-runs only on nightly.
3. Flake quarantine policy? **Recommend**: a flaky test fails the gate
   (no quarantine list); Spec 169 ships a `pytest --flake-bisect`
   helper that bisects the seed for repro.
