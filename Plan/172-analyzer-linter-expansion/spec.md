---
spec_id: "172"
slug: analyzer-linter-expansion
status: draft
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

- [ ] **Typed registry shape: `AxisRegistry{prefixes:
      dict[str, AnalyzerId], resolve(finding_id: str) -> AnalyzerId |
      None, collisions: list[tuple[str, AnalyzerId, AnalyzerId]]}`** —
      exposes the union view + resolution + collisions for inspection.
- [ ] **Invariant: `collisions == []`** for every realistic subset of
      installed analyzers — property test (Spec 050 pattern); ≥ pairwise
      + all-on coverage.
- [ ] **Invariant: longest-prefix-first resolution** — given declared
      prefixes `{"A", "A0"}`, `resolve("A001")` MUST return the analyzer
      owning `"A0"`; not pinned to the current registry.
- [ ] **Invariant: registry is order-independent** — for any
      permutation of installed-analyzer load order, the resulting
      registry's `prefixes` dict + `collisions` list are equal
      (relationship, not pinned).
- [ ] **Invariant: a deliberately-colliding fixture analyzer is
      REJECTED** with `Codes.AXIS_PREFIX_COLLISION` carrying both
      conflicting analyzer ids — proves the guard, not pinned to a
      specific collision.
- [ ] **Relationship: `set(doctor.axis_map.keys()) ==
      set(registry.prefixes.keys())`** for the live registry — Spec
      170 consumer; derived (Spec 149).
- [ ] **Failure mode (registry build):** an analyzer with a malformed
      `AXIS_PREFIXES` (non-string, empty tuple) fails fast with
      `Codes.AXIS_PREFIX_MALFORMED` at registry build, not at first
      use — never silently skipped.
- [ ] TODO row + drift clean.

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
