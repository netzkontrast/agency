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

## Done When (measurable invariants — rule 8)

- [ ] **Typed wrapper shape** — each `_<tool>.py` exports
      `AXIS_PREFIXES: tuple[str, ...]` + `run(target: Path) ->
      list[Finding]` where `Finding = {axis_id, severity, message,
      file, line}` — uniform across mypy/pylint/semgrep.
- [ ] **Invariant: cross-axis prefix collision count == 0** for every
      subset of installed analyzers (registry property test, Spec 172
      sibling).
- [ ] **Invariant: longest-prefix-first resolution holds** — given a
      finding id `MX001`, the resolver picks the analyzer whose declared
      prefix is the longest match (relationship, not pinned).
- [ ] **Invariant: missing-dep silent fallback** — when an analyzer's
      import fails, `analyze.run(axis=<that>)` returns `[]` with a
      ResearchFlag-style hint (not a crash). Asserted by uninstalling the
      dep in a venv subprocess test.
- [ ] **Relationship: `set(doctor.analyze_extras.live)` ==
      `set(installed_wrappers_with_resolvable_import)`** — derived (Spec
      149), never hand-listed.
- [ ] **Spec 157 architecture gate consumes semgrep `agency.cross_cap_import`
      rule** — a verb importing across `agency/capabilities/<other>/`
      fails CI.
- [ ] **Failure mode (external tool path):** when an analyzer crashes
      mid-run (semgrep OOM, mypy daemon hang) the wrapper returns the
      partial Findings collected so far + a `Codes.ANALYZER_PARTIAL`
      Reflection — never a half-empty result silently passed on.
- [ ] TODO row + drift clean.

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
