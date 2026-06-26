---
spec_id: "166"
slug: analyze-deps-extras-expand
status: draft
state: inprogress
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

## Done When (measurable invariants — rule 8)

- [x] **Typed wrapper shape** — `WrapperShape{tool_name, axis_prefixes,
      extras}` derived per external prefix-emitting wrapper via
      `derive_wrapper_shapes()` (composes each module's `EXTERNAL_TOOL` /
      `AXIS_PREFIXES`). `test_wrapper_shapes_are_typed_and_carry_prefixes`.
- [x] **Invariant: cross-axis prefix collision count == 0** — reuses the
      Spec 172 `detect_collisions` sweep over the same analyzer modules
      (live: 0 collisions).
- [x] **Invariant: longest-prefix-first resolution holds** — the Spec 172
      `AxisRegistry` (built longest-first) resolves the wrappers' prefixes.
- [ ] **Invariant: missing-dep silent fallback** — the existing wrappers
      degrade to `[]` when their tool is off PATH (Spec 050); the
      venv-subprocess assertion is DEFERRED (needs an uninstall harness).
- [x] **Relationship: `set(doctor.analyze_extras.live)` ==
      `set(installed_wrappers_with_resolvable_import)`** — `external_tools()`
      DERIVES the tool set from the modules (`EXTERNAL_TOOL`); the doctor's
      `analyze_extras` now iterates it (the prior `AGENCY-DRIFT` tuple is
      retired). `test_external_tools_derive_from_the_modules`.
- [ ] **Spec 157 architecture gate consumes semgrep `agency.cross_cap_import`
      rule** — DEFERRED: needs the semgrep wrapper + the gate wiring.
- [ ] **Failure mode (external tool path):** `Codes.ANALYZER_PARTIAL` +
      mid-run partial-collection — DEFERRED (the 3 new external-tool
      wrappers' run path).
- [x] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  `[analyze]` extra installed including mypy + pylint + semgrep;
        a verb at agency/capabilities/foo/_main.py imports from
        agency/capabilities/bar/_main.py
When:   analyze.run(target="agency/", axes=["A007"]) runs (semgrep
        axis A007 = cross-cap import rule)
Then:   returns Findings[0]{axis_id="A007", severity="error",
        file="foo/_main.py", line=N}; the architecture gate (Spec 157)
        fails CI on the same finding

Given:  `[analyze]` extra installed WITHOUT semgrep (pip uninstall)
When:   analyze.run(axes=["A007"]) runs
Then:   returns [] + agency_doctor.analyze_extras.live excludes "semgrep"
        + a ResearchFlag hint points at `pipx inject agency semgrep`
```

## Failure modes

| Failure | Wrapper response |
|---|---|
| Analyzer dep missing | silent `[]` + doctor hint (Spec 050 pattern) |
| Analyzer crashes mid-run | partial Findings + `ANALYZER_PARTIAL` Reflection |
| Two wrappers declare overlapping prefix | registry build fails (Spec 172) |
| External rule pack out of date | semgrep returns 0 findings — doc-source marker (Spec 054) flags stale |

## Interconnects

- Spec 057 (axis registry) is the substrate this validates.
- Spec 167 (networkx architecture) is the parallel analyzer expansion.
- Spec 157 (architecture gate) is the primary consumer of A007 + A001.
- Spec 172 (registry expansion proof) gates the collision invariant
  every PR.
- Spec 170 (doctor) reports `analyze_extras` (derived).
- Spec 169 (CI coverage + flake gate) consumes Findings for the
  coverage report.
- **Drift-derivation chain** (149): `analyze_extras` derived; rule
  packs carry doc-source markers.
- Spec 151 (Codes coverage) supplies `ANALYZER_PARTIAL`.

## Open questions

1. semgrep rule pack vendored or external? **Recommend**: vendor a
   minimal agency-specific pack (cross-cap import, wire-shape leak);
   external packs opt-in via `userConfig` (Spec 175).
2. mypy strict mode default? **Recommend**: per-capability opt-in;
   blanket strict on a >2000-file repo trips noise — A002 axis surfaces
   per-cap deltas instead of a blanket score.
3. pylint's overlap with ruff? **Recommend**: prefix-segregate — pylint
   axis = the rules ruff does NOT cover (design metrics, R-class); the
   axis registry collision detector keeps them disjoint.

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

### Done — Slice 2 partial (2026-06-26)

The wrapper registry now DERIVES from the modules (no hand-listing):

- `agency/_wrapper_shapes.py`:
  - `external_tools()` — the external CLI-tool set read from each analyzer
    wrapper's `EXTERNAL_TOOL` (the DERIVED replacement for the doctor's
    hand-listed `("ruff","bandit","radon")` tuple — the prior `AGENCY-DRIFT`
    tag is retired).
  - `derive_wrapper_shapes()` — one typed `WrapperShape{tool_name,
    axis_prefixes, extras}` per external prefix-emitting wrapper.
  - `wrapper_shapes_summary()` — `{wrappers, external_tools, shape_tools,
    ready}`.
- `EXTERNAL_TOOL` / `EXTERNAL_EXTRA` declared on `_ruff` / `_bandit` / `_radon`.
- `agency_doctor.analyze_extras` now iterates `external_tools()`; new
  `agency_doctor.wrapper_coverage` field.
- 5 invariant tests in `tests/test_wrapper_shapes.py` (all green): tools derive
  from modules, typed shapes carry prefixes, a new wrapper auto-appears,
  prefix-less tool is a tool not a shape, summary matches the doctor derivation.

### Still — deferred (the linter-expansion headline)

- The three NEW external wrappers (`_mypy` / `_pylint` / `_semgrep`) +
  `analyze.run` integration — needs the tools installed + a venv-subprocess
  missing-dep fallback test.
- Spec 157 gate consuming semgrep `agency.cross_cap_import`.
- `Codes.ANALYZER_PARTIAL` + mid-run partial-collection on the external path.

**Verdict:** PARTIAL — the derivability invariant (the spec's headline:
`analyze_extras` derived, never hand-listed) + the typed `WrapperShape` registry
shipped, killing a real `AGENCY-DRIFT`; the mypy/pylint/semgrep expansion + the
semgrep gate remain.

