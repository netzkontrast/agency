---
spec_id: "172"
slug: analyzer-linter-expansion
status: done
state: done
last_updated: 2026-06-10
owner: "@agency"
enhances: "057"
depends_on: ["057", "166", "167", "149"]
vision_goals: [4]
affects:
  - agency/capabilities/analyze/_main.py
  - tests/test_axis_registry_expansion.py
---

# Spec 172 — analyzer rule-axis registry expansion proof

## Why

Spec 057 made the analyzer axis registry drop-in (each `_<tool>.py`
declares `AXIS_PREFIXES`; the registry unions with longest-prefix-first
+ cross-axis collision detection). Specs 166 + 167 add mypy/pylint/
semgrep/networkx. This spec is the REGISTRY-level proof that the
expansion didn't break the union invariant — a standing test that the
registry rebuilds clean for ANY combination of installed analyzers, so
future linters drop in without a registry edit.

## Done When (measurable invariants — rule 8)

- [x] **Typed registry shape: `AxisRegistry{prefixes, resolve(...)}` +
      `collisions` view** — Slice 1 shipped the typed shape;
      `derive_axis_registry` (Slice 2) populates it from the live
      wrappers + `detect_collisions` exposes the collisions view.
- [x] **Invariant: `collisions == []`** for the live + fixture subsets —
      `test_live_registry_has_no_collisions` + `detect_collisions`
      property tests (pairwise fixture + all-on live).
- [x] **Invariant: longest-prefix-first resolution** — the registry is
      built sorted longest-first, so `resolve("A001")` returns the owner
      of `"A0"`. `test_longest_prefix_first_resolution`.
- [x] **Invariant: registry is order-independent** — every permutation
      of load order yields the identical `prefixes` tuple.
      `test_registry_is_order_independent`.
- [x] **Invariant: a deliberately-colliding fixture analyzer is
      REJECTED** with `Codes.AXIS_PREFIX_COLLISION` carrying both
      conflicting axes. `test_colliding_fixture_is_rejected`.
- [x] **Relationship: doctor reports the live registry** —
      `agency_doctor.axis_registry_coverage {ready, entries, collisions}`
      consumes `axis_registry_summary` (Spec 170 consumer; derived).
- [x] **Failure mode (registry build):** a malformed `AXIS_PREFIXES`
      (non-string / empty prefix) fails fast with
      `Codes.AXIS_PREFIX_MALFORMED` at build.
      `test_malformed_prefix_fails_fast`.
- [x] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  installed analyzers = {ruff(R), bandit(B), radon(C), mypy(M),
        pylint(P), semgrep(S), networkx(A)} — Specs 050 + 166 + 167
When:   AxisRegistry.build(analyzers) runs the property test over
        every pairwise subset + the all-on combination
Then:   for every subset, collisions == [] AND resolve("A001") ==
        networkx_id AND resolve("B101") == bandit_id AND
        registry is byte-identical across load-order permutations

Given:  a fixture analyzer declares AXIS_PREFIXES=("R",) (collides
        with ruff)
When:   AxisRegistry.build(...{fixture, ruff,...}) runs
Then:   raises AXIS_PREFIX_COLLISION carrying ("R", ruff_id,
        fixture_id); registry build aborts (never partial)

Given:  a fixture analyzer declares AXIS_PREFIXES=()
When:   build runs
Then:   raises AXIS_PREFIX_MALFORMED at build time — never at first
        finding-id resolution
```

## Failure modes

| Failure | Registry response |
|---|---|
| Two analyzers declare same prefix | `AXIS_PREFIX_COLLISION` — build aborts; both ids surfaced |
| Empty / non-string prefix | `AXIS_PREFIX_MALFORMED` at build |
| Load-order produces different registry | property test catches; Spec 169 flake gate also catches |
| Analyzer crashes at probe (collision check) | wrapper's `Codes.ANALYZER_PARTIAL` (Spec 166) — registry build still completes for the others |
| New analyzer's prefix collides with a planned axis (e.g. Spec 178+) | property test fails on the planned-axis fixture |

## Interconnects

- Spec 166 (mypy/pylint/semgrep) + Spec 167 (networkx) are the
  expansion this guards.
- Spec 057 is the parent substrate.
- Spec 169 (CI coverage + flake gate) — re-runs the property test
  twice as a flake check.
- Spec 170 (doctor) reports the live axis map (derived).
- Spec 151 (Codes coverage) supplies `AXIS_PREFIX_COLLISION` +
  `AXIS_PREFIX_MALFORMED`.
- **Drift-derivation chain** (149): axis map derived; doctor + the
  README capability table consume it.
- Spec 167 (architecture) — the A-axis namespace this registry
  guards.

## Open questions

1. Power-set test too slow at N analyzers? **Recommend**: cap at
   pairwise + all-on (the collisions that matter are pairwise); a
   triple-collision implies two pairwise collisions already caught.
2. Property test on shipped analyzers only, or include planned axes?
   **Recommend**: include planned-axis fixtures (Spec 178+) so adding
   a future analyzer doesn't trip a hidden collision late.
3. Allow override of resolution order? **Recommend**: no — the
   longest-prefix-first rule is wire-shape (Spec 019); overrides break
   the resolution invariant.

## Followup — Implementation Status (Slice 1, 2026-06-12)

**Verdict:** Slice 1 SHIPPED on `claude/autonomous-completion` as part of
the wave-1 typed-shape batch-2 (intent:2219e694; engine-driven tdd walk).

### Done — Slice 1 (typed shape)

Typed frozen dataclass + `__post_init__` invariants in
`agency/_typed_shapes_wave1_part2.py`; tests in
`tests/test_typed_shapes_wave1_part2.py` (17 tests total across the
8-spec batch). Slice 2 wires each shape into its consuming runtime
(red-team rerunner, CLI projection, derive audit, wrapper modules,
networkx metric, axis registry, migration walker, ref audit).

### Done — Slice 2 (2026-06-26)

The axis-registry deriver is built and consumed:

- `agency/_axis_registry_sweep.py`:
  - `derive_axis_registry(modules=None)` — composes every live analyzer
    wrapper's `AXIS_PREFIXES` into the typed `AxisRegistry`, prefixes sorted
    **longest-first** (longest-prefix-first resolution) and **order-
    independent**. Raises on collision.
  - `detect_collisions(modules=None)` — pairwise prefix-collision report
    (same prefix, different axes); same-axis overlaps idempotently unioned.
  - `axis_registry_summary(modules=None)` — non-raising doctor roll-up
    `{ready, entries, collision_count, collisions, code}`.
- `Codes.AXIS_PREFIX_COLLISION` + `Codes.AXIS_PREFIX_MALFORMED` added.
- `agency_doctor.axis_registry_coverage {ready, entries, collisions}`
  consumes the sweep. Live: `{ready: true, entries: 20, collisions: 0}`.
- 7 invariant tests in `tests/test_axis_registry_sweep.py` (all green):
  Codes, live-no-collisions, longest-prefix-first, order-independence,
  collision rejection, malformed fail-fast, same-axis-overlap-not-collision.

The deriver composes the SAME analyzer set `analyze/_main.py::
_build_axis_registry` unions, so the derived registry and the live lookup
cannot drift (rule 2).

**Verdict:** Slice 2 SHIPPED. `scripts/check-drift` clean.

