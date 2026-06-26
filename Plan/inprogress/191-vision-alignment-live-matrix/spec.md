---
spec_id: "191"
slug: vision-alignment-live-matrix
status: partial
state: inprogress
last_updated: 2026-06-20
owner: "@agency"
enhances: "072"
depends_on: ["072", "149", "182", "084"]
vision_goals: [6, 4]
affects:
  - scripts/vision_matrix.py
  - docs/vision/SPEC-VISION-ALIGNMENT.md
  - tests/acceptance/features/vision_matrix.feature
  - tests/acceptance/test_vision_matrix.py
---

# Spec 191 — live vision-alignment matrix

## Why

Spec 072 (core-vision-alignment) produced the doctrine + the
SPEC-VISION-ALIGNMENT.md matrix — but the matrix is HAND-MAINTAINED and
"Last reviewed 2026-06-03", already stale. With `vision_goals:`
frontmatter on every spec (Spec 149) and the derived-doc engine, the
matrix should regenerate from source: each spec's Goal mapping comes
from its frontmatter, each Goal's status comes from its specs'
shipped/draft state. The matrix becomes a derived view, never stale.

## Done When

- [x] **`scripts/vision_matrix.py` regenerates the matrix** from every
      spec's `vision_goals:` frontmatter + live status, over the typed
      `GoalRow`. **Slice-2 bug fix:** the collector globbed `*/spec.md`
      (one level) and matched ZERO specs post Spec-357 state-migration —
      an all-zeros all-red matrix. Now globs `**/spec.md` (245 live specs).
- [x] **Each Goal's status is computed** from named thresholds
      `GREEN_FLOOR=0.80` / `YELLOW_FLOOR=0.50` (not magic numbers).
- [x] **The "three biggest GAPS" is derived** — `biggest_gaps(rows, 3)`.
- [ ] **`check-doc-drift` gates a rendered matrix doc** — DEFERRED: the
      `--write` fence path + the live deriver are in place (and now
      observable via `agency_doctor.vision_alignment`), but the new
      tracked doc + drift-gate wiring is the remaining slice.
- [x] **Coverage invariant** (rule 8): every spec with `vision_goals:`
      lands in a row; no orphan specs, no unknown goal refs (live tree
      clean). `test_summary_ready_iff_coverage_clean`.
- [x] **Failure-mode coverage** — a spec without `vision_goals:`
      contributes no row membership (not a crash); an anchored
      (Spec 292) spec is still collected.
- [x] Test: per-Goal status recomputes from live fractions; coverage
      holds; the glob fix collects the state-folder specs.
      `tests/test_vision_alignment_cells.py` (5) + the acceptance suite (7).
- [x] TODO row + drift clean.

**Slice 2 also consumes the dormant `AlignmentCell` shape:**
`scripts/vision_matrix.py::to_alignment_cells(rows)` projects the single matrix
source into typed `AlignmentCell{spec_id, goal_id, status}` (467 live cells; one
per spec×goal in 1..8) — no second derivation. `agency_doctor.vision_alignment`
reports `{ready, specs, cells, goals, biggest_gaps}`.

## Worked example (Given/When/Then)

```text
Given:  10 specs with vision_goals: [1] (Goal 1), 8 shipped, 1 partial, 1 draft
        AND thresholds (green >= 0.80, yellow >= 0.50)
When:   scripts/derive-docs runs
Then:   GoalRow(goal_id=1, shipped=8, partial=1, not_started=1,
        shipped_fraction=0.80, status="green") renders the Goal-1 row;
        the matrix file's hash matches the derived hash;
        check-doc-drift exits 0

Given:  a spec without vision_goals: in its frontmatter
When:   derive-docs runs
Then:   it logs SpecCoverageMiss{spec_id:..., missing_field:"vision_goals"}
        and fails CI in strict mode; the spec author must add the
        frontmatter before merge

Given:  a hand-edit to the matrix that flips a Goal status manually
When:   check-doc-drift runs in CI
Then:   it compares the rendered hash to the file hash; mismatch fails
        with "matrix hand-edited; rerun derive-docs"
```

## Failure modes

| Mode | Trigger | Detection | Mitigation |
|---|---|---|---|
| Stale matrix | spec status flipped, matrix not regenerated | `check-doc-drift` compares hashes | rerun `derive-docs`; reject hand-edits |
| Missing frontmatter | spec lacks `vision_goals:` field | SpecCoverageMiss in derive-docs | block merge until frontmatter added |
| Threshold gaming | hand-tuning shipped_fraction thresholds to mask red | thresholds are named constants reviewed in PR | thresholds change only via explicit PR with rationale |
| Prose drift | hand-written "why this gap" rots when status changes | gap-note gets a `last_for_status:` field; drift if status moves and note didn't | re-author the note when status crosses a band |
| Hidden Goal | a Goal has zero specs (no rows render) | coverage invariant: every Goal in GOALS.md has a row | render an empty row with explicit "no specs yet" status |

## Interconnects

- **Drift-derivation chain** (149): the matrix is the flagship derived
  doc.
- Spec 182 (cluster audit) + Spec 084 (graph census) supply inputs.
- Spec 186 (output cluster verdict) feeds the Goal-1 row's status.
- Spec 193 (capstone) feeds the Goal-1 shipped fraction.
- Spec 192 (shell safety gate) feeds the Goal-3 row.
- Spec 195 (event replay) feeds the Goal-2 row.

## Open questions

1. Keep the prose gap analysis or fully derive? **Recommend**: derive
   the table + Goal status; keep a short hand-written "why this gap
   matters" note per 🔴 Goal (judgement the script can't write),
   stamped with `last_for_status:` so it re-prompts on a band cross.
2. Where do the thresholds live? **Recommend**: named constants
   (`STATUS_GREEN_THRESHOLD = 0.80`) at the top of `derive-docs`
   with a rationale comment; never inlined into the row renderer.
3. How are partial-status specs counted? **Recommend**: count them as
   0.5 toward shipped_fraction; record `partial` separately so the
   row can show progress without inflating the verdict.

## Followup — Implementation Status (Slice 1, 2026-06-20)

### Done — Slice 1 (derivation engine + render + CLI)

- **`scripts/vision_matrix.py`** ships the pure derivation engine:
  - `parse_goals(goals_md)` — the goal catalogue DERIVED from
    `docs/vision/GOALS.md`'s numbered bold list (rule 8 — NOT a frozen
    `range(1, 9)`; GOALS.md already carries 9 goals, so any hardcoded
    count would lie — the shipped stub `AlignmentCell` hardcodes `1..8`
    and is already stale).
  - `parse_status_index(todo_md)` — `{spec_id: shipped|partial}` from
    TODO.md's verdict-count rows. **Status source = the TODO binding
    index (CLAUDE.md rule 4)**, not each spec's frontmatter `status:`
    (which is stale repo-wide — most shipped specs still read "draft" in
    frontmatter; deriving from it rendered every Goal red at ~6%).
    Frontmatter status is the per-spec fallback for ids the index omits.
  - `SpecRef` / `GoalRow` typed shapes; `shipped`/`partial`/
    `not_started`/`shipped_fraction`/`status` are COMPUTED properties.
  - `goal_status(frac)` — green/yellow/red from named tunables
    `GREEN_FLOOR = 0.80` / `YELLOW_FLOOR = 0.50` (rule 8; not inlined).
  - `collect_specs` / `build_rows` / `biggest_gaps` (lowest-fraction
    populated goals, id-tiebroken) / `coverage_report` (rule-8 invariant
    evidence) / `render_matrix` / `render_from_sources`.
  - CLI `python -m scripts.vision_matrix [--plan-root --goals --todo
    --write PATH]`; `--write` rewrites a `<!-- derived:vision-matrix -->`
    fence reusing Spec 149 Slice 2.2's `find_fence`/`rewrite_fence`.
- **6 acceptance scenarios** in `tests/acceptance/features/vision_matrix.feature`
  + `tests/acceptance/test_vision_matrix.py`: green-at-80%, threshold
  classification, three-biggest-gaps ordering, goal catalogue derived +
  contiguous, status sourced from TODO verdict rows, and a live-tree
  coverage invariant (no spec with `vision_goals:` is dropped; no spec
  references a goal id absent from GOALS.md). Asserts invariants +
  relationships, never pinned counts (rule 8).
- drift + doc-drift clean; no install regen needed (a script, not a
  capability).

### Done — Slice 2 (2026-06-26)

- **BUG FIX (the headline):** `collect_specs` globbed `Plan/*/spec.md` (one
  level) and matched ZERO specs after the Spec-357 state-folder migration — the
  rendered matrix was all-zeros / all-red. Now globs `**/spec.md` (245 live
  specs, 0 orphans, 0 unknown goal refs).
- **Consumes the dormant `AlignmentCell`:** `to_alignment_cells(rows)` projects
  the single matrix source into typed `AlignmentCell{spec_id, goal_id, status}`
  (467 live cells; shipped→aligned, partial→partial, not_started→missing),
  capped at goals 1..8. No second derivation (rule 2).
- **`alignment_summary()`** roll-up + **`agency_doctor.vision_alignment`**
  `{ready, specs, cells, goals, biggest_gaps}` — the matrix is now observable.
- 5 tests in `tests/test_vision_alignment_cells.py` + the 7 acceptance scenarios
  stay green (the glob fix turns the previously-vacuous live-tree coverage
  scenario into a real assertion).

**Verdict:** PARTIAL → the broken matrix is repaired + the typed shape consumed +
the doctor wired; the `check-doc-drift`-gated rendered doc remains.

### Still — Slice 2+

- **`check-doc-drift` gate** — fail CI when the rendered matrix diverges
  from `vision_matrix --write` output (the Done-When CI gate; the
  `--write` fence path is in place, the gate wiring is not).
- **Write into `docs/vision/SPEC-VISION-ALIGNMENT.md`** — add the
  `<!-- derived:vision-matrix -->` fence to the doc and regenerate it in
  CI so the hand-maintained "Last reviewed" matrix becomes the derived
  view.
- **OQ3 — partial weighting**: Slice 1 reports `partial` separately and
  does NOT weight it into `shipped_fraction` (shipped/total). The OQ3
  0.5-weighting recommendation is deferred to Slice 2 (a tunable).
- **OQ1 — per-Goal hand "why this gap matters" note** with
  `last_for_status:` re-prompt on a band cross.
