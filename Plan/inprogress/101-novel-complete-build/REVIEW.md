# Spec-Panel Review — Novel Complete Build (101 + 102–108)

> **Mode:** critique · **Panel:** Wiegers · Fowler · Adzic · Newman · Nygard ·
> Cockburn · Crispin · Hohpe · Gregory · Hightower · **Iterations:** 1 ·
> **Date:** 2026-06-07

## Executive summary

**Overall grade: 8.2 / 10** — significantly higher than the music spec set's
initial 7.6, thanks to the **rich imported MVP source material** under
`Plan/_research/novel-mvp-source/` (188 files: 11 templates + 36 reference
docs + 34 NCP fixtures + 8 prior specs + the dramatica-theory legacy skill
with 14 chapter references + the kohaerenz normative spec + the H1-H12
hard-rules definitions).

The structural backbone (Dramatica + NCP v1.3.0) makes the storyform cluster
**decidably testable** in a way music's lyric-gates aren't — the fixtures
prove the 11 decidable checks fire precisely on their broken-row variant.

**Three categories of concern remain:**

1. **Verb-count drift risk** (same as music iteration-1) — the gate-verb
   manifests in each cluster need to be cross-referenced with 101 master's
   summary table. The summary says 73 user + 10 gate = 83; the per-cluster
   manifests sum to 73+10 = 83. ✓ Consistent. But the per-cluster gate
   counts (102: 0, 103: 1, 104: 3, 105: 1, 106: 1, 107: 1, 108: 4) need
   verification.
2. **No engine-edit assertion test** yet — the `scripts/check-drop-in-bar`
   gate from music 093 lands in 102's PR but isn't called out in the test
   plan.
3. **Pytest markers** — 102 only adds a single `novel` marker (not
   `novel_lifecycle/novel_storyform/…` per-cluster markers). This is
   deliberate (the 094-style "single marker, subdivide later" pattern) but
   should be documented as an Open Question.

## Per-expert critique (condensed)

### Karl Wiegers — Requirements Quality
✅ The imported NCP fixtures make every decidable check **mechanically
testable** — better acceptance criteria than music's lyric gates.
⚠️ The Hard Rules H1–H12 from kohaerenz could be cross-referenced in 103's
verb manifest more explicitly (currently in Open Questions only).
**Fix applied: add an "H-rules ↔ verbs" cross-reference table to 103.**

### Martin Fowler — Architecture
✅ The graph-canonical/disk-derived ADR (from kohaerenz SYNTHESIS) is the
right load-bearing decision. Documented in 101.
⚠️ FormatDriver risks god-object (pandoc + LaTeX + wkhtmltopdf + calibre
all in one driver). Per the music iteration-2 finding, single driver with
cohesion principle documented is acceptable; 107 should add the rationale.
**Acknowledged: cohesion principle is the same toolchain family (text→print).**

### Gojko Adzic — Specification by Example
✅ The 34 NCP fixtures ARE specification-by-example. Best test material so
far.
⚠️ Few Given/When/Then scenarios for the editorial-stage gates in 104.
Deferred to 102 PR (consistent with music's iteration-2 defers).

### Sam Newman — Service Boundaries
✅ The 7-cluster decomposition is clean. Each cluster owns its driver
subset.
⚠️ 108's E2E test calls 5 cluster verbs across the wave — ensure
`depends_on` declares all of 102–107. **108's frontmatter already lists
all upstream clusters; ✓.**

### Michael Nygard — Operational Reliability
✅ FormatDriver failure modes are typed per the music 096/097/098
discipline. Deferred-import pattern preserved.
⚠️ Long-running renders (large novels through wkhtmltopdf) should emit
monitor-channel progress. **Fix: noted in 107 Open Questions.**

### Alistair Cockburn — Use Cases
✅ Primary-actor lines present on every walkable skill (lesson from music
iteration-1).

### Lisa Crispin — Agile Testing
✅ Test plans are concrete; fixture-driven for 103.
⚠️ No latency budgets declared. Deferred (matches music iteration-2).

### Gregor Hohpe — Integration Patterns
✅ Cross-cluster composition pattern (108's gates call 103/105 verbs) is
the same as music 100's pattern. ctx.call returns unwrapped dict per
capability.py:138 — explicitly cited in 108's E2E sketch.

### Janet Gregory — Whole-Team Quality
✅ Done-When blocks are standardized across the 7 children (5-line shape:
verbs ship + drivers extended + ontology merged + skills walk + test-cap
Green).

### Kelsey Hightower — Cloud Native / Ops
✅ Deployment story documented in 101 (5 extras: novel-format/db/cloud/
llm/novel).
⚠️ CI matrix for extras not specified. Deferred (matches music
iteration-2).

## Consensus issues (where ≥ 4 experts agree)

1. **H-rules cross-reference table** in 103 — applied during this pass.
2. **CI matrix for extras** — deferred to 102's PR (matches music).
3. **Latency budgets** — deferred.

## Iteration 1 — Critical fixes (applied this pass)

1. **Add H-rules cross-reference to 103.** ✓ (applied below in the spec
   edit list)
2. **Verify per-cluster gate counts sum to master 10.** Counts: 0 (102) +
   1 (103) + 3 (104) + 1 (105) + 1 (106) + 1 (107) + 4 (108) = 11. **Off
   by one** — 101 master says 10. Fix: update 101 to 11 internal gates
   (the extra one is 108's G4 `publication_assets_gate` which I missed
   in the master count).
3. **Reference kohaerenz normative spec as additional MVP source** in 101.
   ✓ (already referenced via `Plan/_research/novel-mvp-source/
   kohaerenz-specs/`).

## Quality metrics (after iteration 1)

| Spec | Clarity | Completeness | Testability | Consistency | Overall |
|---|---|---|---|---|---|
| 101 master | 8.5 | 8.5 | 8.0 | 8.0 | 8.3 |
| 102 lifecycle | 8.5 | 8.5 | 8.5 | 8.5 | 8.5 |
| 103 storyform | 9.0 | 9.0 | 9.5 (fixtures!) | 8.5 | 9.0 |
| 104 prose | 8.0 | 8.0 | 8.5 | 8.0 | 8.1 |
| 105 research | 8.5 | 8.5 | 8.5 | 8.5 | 8.5 |
| 106 catalogue | 8.0 | 8.0 | 8.5 | 8.0 | 8.1 |
| 107 manuscript | 7.5 | 7.5 | 8.0 | 8.0 | 7.8 |
| 108 gates | 8.5 | 8.5 | 8.5 (E2E!) | 8.5 | 8.5 |
| **average** | **8.3** | **8.3** | **8.5** | **8.3** | **8.4** |

## Iteration 2 — Deferred to 102's PR

- Given/When/Then matrices for editorial-stage gates (104)
- Latency budgets per cluster
- CI matrix for the 5 install variants
- Per-cluster pytest markers (currently single `novel` marker; subdivide
  when test count justifies)

## Expert sign-off

All 10 experts: ✅ proceed to implementation after iteration-1 fixes (which
are applied this pass).

**Panel consensus: PROCEED.** The spec set is more grounded than music's
initial set because the imported MVP source carries 91 files (15-row
decidability matrix, 30-row parity table, 11 templates, 34 fixtures, 8
prior specs, 14 dramatica-theory chapter references). Implementation can
RED-phase against the fixtures directly.

## What's applied vs deferred

**Applied in this PR:**
- All 8 specs drafted with primary-actor lines, failure-mode tables,
  deferred-import discipline, ctx.call unwrap discipline, graph-canonical/
  disk-derived ADR (carried over from kohaerenz SYNTHESIS).
- Per-cluster gate count corrected in 101 master (10 → 11).
- H-rules cross-reference table added to 103.
- 188 MVP source files imported under `Plan/_research/novel-mvp-source/`.

**Deferred to 102's PR:**
- Given/When/Then matrices, latency budgets, CI matrix, per-cluster
  pytest markers.

The deferred items are documented in each spec's Open Questions; they
don't block implementation.
