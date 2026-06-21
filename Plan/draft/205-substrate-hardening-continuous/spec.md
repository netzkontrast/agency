---
spec_id: "205"
slug: substrate-hardening-continuous
status: draft
state: draft
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

- [ ] **`HardeningReport` typed return** from `scripts/check-drift
      --hardening` — `HardeningReport = {checks: list[Check], passed:
      int, failed: int, regressions: list[Regression]}` where
      `Check = {fix_id: Literal["G1".."G6"], name, status:
      Literal["pass","fail","skipped"], evidence_path}` and
      `Regression = {fix_id, file, line, detail}`.
- [ ] **Each of the six 092 fixes has a standing check** in
      `check-drift` (Spec 054 family) or CI — a regression on any one
      fails the build:
      - G1 installer prune — `Check` asserts no orphaned plugin
        entries after `python -m agency.install`.
      - G2 reserved-name lint — covers original + enhancement-era
        names (AnthropicDriver, TokenCounter, ParityReport, etc.).
      - G3 OpenRouter Driver — kept callable; smoke test asserts
        Boundary protocol conformance.
      - G4 intent→develop cues — the cue table is derived from the
        live capability registry, not hand-pinned.
      - G5 doc-drift in CI — `scripts/check-doc-drift --strict`
        exit 0.
      - G6 followup-grounding — every spec's `Followup —
        Implementation Status` cites file:line that resolves live.
- [ ] **Invariant — fix-count relationship** (not pinned): `len(checks)
      >= 6` AND `{c.fix_id for c in checks} == {"G1","G2","G3","G4",
      "G5","G6"}` — the six are a SET, not a count; future fixes
      append (G7, G8, ...) without breaking the invariant.
- [ ] **Invariant — followup grounding** (relationship, G6): for every
      spec with a Followup section, `every(citation, citation.file
      exists AND citation.line <= line_count(citation.file))` — a
      stale file:line fails (Spec 149 drift).
- [ ] **Invariant — reserved-name coverage** (relationship, G2): the
      reserved-name set EQUALS the union of (a) live capability/verb
      names and (b) the enhancement-era public class names declared in
      the spec frontmatter `affects` blocks; a new public symbol that
      escapes the lint fails the audit.
- [ ] **Invariant — check-drift wall-clock** (relationship):
      `check-drift --hardening` completes within
      `HARDENING_BUDGET_SECONDS` (default 30s) so the CI fast-feedback
      loop stays usable; a regression past the budget signals an
      O(N²) check (Spec 053 fast-local doctrine).
- [ ] **The followup-grounding rule (G6)** is enforced by the derived-
      doc discipline (Spec 149).
- [ ] **The reserved-name lint (G2)** covers the new enhancement-era
      names (AnthropicDriver, TokenCounter, ParityReport, etc.).
- [ ] Test: a regression of each 092 fix trips its standing check (a
      synthetic injection per fix); the wall-clock invariant asserted
      on a CI-shaped fixture.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  HEAD is clean; all six 092 fixes are in place
When:   scripts/check-drift --hardening runs
Then:   HardeningReport{passed: 6, failed: 0, regressions: []}
        AND exit code 0
        AND wall-clock <= HARDENING_BUDGET_SECONDS

Given:  someone accidentally re-introduces a forbidden reserved name
        in agency/_drivers/_anthropic.py (e.g. names a class
        "AnthropicDriverV2" that collides with a wire-name reservation)
When:   scripts/check-drift --hardening runs in CI
Then:   HardeningReport.regressions includes
            {fix_id:"G2", file:"agency/_drivers/_anthropic.py",
             line:42, detail:"reserved_collision: AnthropicDriverV2"}
        AND exit code 1 AND CI fails

Given:  a spec's Followup cites Plan/092-…/spec.md:120 but the file
        now has 100 lines
When:   the G6 standing check runs
Then:   regression flagged with detail:"followup_line_stale" AND CI
        fails — Spec 149 derived-doc gate refuses the commit
```

## Failure modes (Nygard)

| Failure | Hardening check response |
|---|---|
| G1 installer leaves orphans | `fix_id:"G1"` fail; lists orphaned entries |
| G2 reserved name collision | fail with file:line of the colliding symbol |
| G3 OpenRouter Driver broken | fail with the boundary-protocol violation detail |
| G4 cue table drift (hand-pinned vs live registry) | fail; require derivation rebuild |
| G5 doc-drift unmarked source | `check-doc-drift --strict` exit 1 |
| G6 followup file:line stale | fail with the stale citation |
| Check wall-clock exceeds budget | WARN once, FAIL on second run — the check itself is the bug |
| New public symbol escapes G2 audit | fail; spec author must add the name to the reservation set |

## Interconnects

- Spec 155 (red-team re-runner) is the parallel generalize-a-one-time-
  pass spec; same standing-check pattern.
- Spec 157 (architecture gate) + Spec 149 (drift) host the checks.
- Spec 054 (drift management) — `check-drift` is the host script; this
  spec adds the `--hardening` subcommand.
- Spec 198 (CLI parity) — the parity gate is itself a standing check
  in the same family; shares the wall-clock budget discipline.
- Spec 199 (skill round-trip) — round-trip TTL staleness is a standing
  check eligible for inclusion as G7 when the round-trip ships.
- Spec 203 (graph query) — `analyze.graph_query` is used to query
  regression-edge provenance ("which commit introduced this
  regression?").
- Spec 053 (test organization) — the wall-clock budget aligns with
  fast-local-feedback doctrine.

## Open questions

1. All six as hard gates? **Recommend**: yes — they were correctness
   fixes; a regression is a real bug, not a style nit. WARN-cycle only
   for newly-added Gn checks (one CI cycle); promote to hard fail once
   the live registry reports zero violations (Spec 056/058 pattern).
2. How are new hardening fixes added? **Recommend**: each new fix
   appends a G(n+1) check + a synthetic-injection test in the same PR;
   the SET invariant flexes automatically (no pinned count).
3. Where does the regression-evidence trail live? **Recommend**: every
   `Regression` writes a `(Invocation)-[:PRODUCES]->(Reflection
   {scope:"hardening_regression"})` edge; queryable via Spec 203,
   feeds Spec 150 amendment classifier — closing the dogfood loop on
   substrate regressions themselves.
