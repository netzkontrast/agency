---
spec_id: "191"
slug: vision-alignment-live-matrix
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "072"
depends_on: ["072", "149", "182", "084"]
vision_goals: [6, 4]
affects:
  - docs/vision/SPEC-VISION-ALIGNMENT.md
  - scripts/derive-docs
  - tests/test_vision_matrix_derived.py
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

- [ ] **`scripts/derive-docs` regenerates the matrix** from every
      spec's `vision_goals:` frontmatter + live status (Spec 149).
      The renderer reads a typed `GoalRow{goal_id:int, title:str,
      specs:list[SpecRef], shipped:int, partial:int, not_started:int,
      shipped_fraction:float, status:Literal["green","yellow","red"]}`
      per Goal and the source list per row.
- [ ] **Each Goal's status is computed** from the shipped-fraction
      thresholds (documented tunables): `green if frac >= 0.80,
      yellow if frac >= 0.50 else red`. Thresholds are named constants
      in the script, not magic numbers in row code.
- [ ] **The "three biggest GAPS" section is derived** — `sorted(goals,
      key=lambda g: g.shipped_fraction)[:3]`, recomputed on every
      `derive-docs` invocation.
- [ ] **`check-doc-drift` gates the matrix** against the frontmatter:
      `hash(rendered_matrix) == hash(rendered_from_current_sources)`
      OR CI fails with the drift kind named.
- [ ] **Coverage invariant** (rule 8): every spec with `vision_goals:`
      in its frontmatter appears in at least one Goal row; every Goal
      with at least one spec has a non-empty row. No orphan specs, no
      empty Goals.
- [ ] **Failure-mode coverage** for missing frontmatter, stale matrix,
      and prose-vs-data drift.
- [ ] Test: flip a spec's status → the matrix Goal status recomputes;
      drift catches a stale matrix; a spec missing `vision_goals:` is
      flagged.
- [ ] TODO row + drift clean.

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
