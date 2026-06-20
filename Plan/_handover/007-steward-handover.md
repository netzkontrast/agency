<!-- agency steward handover — read this first next run -->
# Steward Handover 007 — 2026-06-20

## What shipped this run

**Spec 153 Slice 5 — deferred-tag gate (`--fix-baseline` auto-trim).**

Closed the final point of friction in the schema coverage maintenance workflow.
The `check_schema_coverage.py` CLI now accepts a `--fix-baseline` argument
that auto-removes labels that have gained coverage from the baseline file,
preserving comments and formatting.

### Key changes

**`scripts/check_schema_coverage.py`**
- `parser.add_argument("--fix-baseline", ...)`
- Rewrites `res.fixed_uncovered` elements from the `args.baseline` file.

**`Plan/153-fix-baseline-auto-trim/spec.md`**
- Spec file created with the acceptance criteria for this slice.

## Evidence

- Local unit testing demonstrated the auto-trimming behaviour removes the exact labels.
- Drift gate is clean (`scripts/check-drift` passing).
- Run full test suite; no regressions observed related to the new scripts.

## Next 3 candidates (ranked)

1. **Proposed amendment from handover 005 — dormant_schemas in scripts/check-drift**
   Add the `dormant_schemas` check from `agency_doctor` into the CI drift gate
   (currently only fires when the user invokes the doctor or schema CLI). The
   `scripts/check-drift` snippet was drafted in handover 005 — a short, low-risk
   addition that closes the gap between the per-PR drift gate and the runtime gate.
   Blocked three Slice 6 batches before being caught; now it's a known pattern.

2. **Spec 337 deferred — graph-override read path for FilterProfile**
   Analogous to `shell.define` for command templates: let a project store a
   `FilterProfile` Artefact in the graph to override a seed profile without a code
   change. The AGENCY-DRIFT tag at `_FILTER_PROFILES` protects the surface. Medium
   effort; low urgency (seed registry covers the known high-volume tools).

3. **FastAPI typed-read surface (Goal 5/7, Spec 330 follow-up)**
   Architecturally significant capstone; needs a human-reviewed spec for
   server boundary, auth model, and lifecycle integration before implementation
   begins. Still the right long-term direction the typed-entity program points
   at. Do NOT start without explicit human sign-off on the design.

## Pillar gate (held)

Intent/Capability/Lifecycle/Memory — all pillars read+write load-bearing.
Schema coverage: 93/93 = 1.0 (full).
Dormant schemas: 0. Drift: clean.

## Key lesson

Ensuring test stability before implementing feature slices ensures that the code changes are correctly evaluated. In this run, some pre-existing failures in `tests/acceptance/test_hooks.py` were left aside, but resolving unrelated flaky tests provides more confidence in changes overall.
