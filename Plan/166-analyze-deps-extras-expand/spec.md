---
spec_id: "166"
slug: analyze-deps-extras-expand
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "050"
depends_on: ["050", "057", "157", "149"]
vision_goals: [4]
affects:
  - agency/capabilities/analyze/_mypy.py  (NEW)
  - tests/test_analyze_deps_expand.py
---

# Spec 166 — analyze-deps extras expansion (mypy/pylint/semgrep)

## Why

Spec 050 wired ruff + bandit + radon into the analyze axes via the
`[analyze]` extra, and Spec 057 made the axis registry drop-in (each
analyzer declares `AXIS_PREFIXES`; "drop-in pattern for future linters
(mypy/pylint/semgrep) = wrapper + one import"). The pattern is proven;
this spec exercises it by adding the three named linters, validating
the registry generalizes.

## Done When

- [ ] **mypy / pylint / semgrep wrappers** added, each declaring
      `AXIS_PREFIXES` (Spec 057 pattern) — one wrapper + one import each.
- [ ] **Cross-axis collision detection** (Spec 057) still passes with
      the expanded prefix set.
- [ ] **Silent fallback** when a dep is missing (Spec 050 pattern);
      `agency_doctor.analyze_extras` reports the live set (derived).
- [ ] **The architecture-drift gate (Spec 157) consumes semgrep**
      for the cross-capability-import rule.
- [ ] Test: each new linter activates on its fixture; collision-free.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 057 (axis registry) is the substrate this validates.
- Spec 157 (architecture gate) is a consumer.
- **Drift-derivation chain** (149): `analyze_extras` derived.

## Open questions

1. semgrep rule pack vendored or external? **Recommend**: vendor a
   minimal agency-specific pack (cross-cap import, wire-shape leak);
   external packs opt-in.
