---
spec_id: "261"
slug: vision-charter-closing-audit
status: draft
state: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "_planning/charter"
depends_on: ["191", "149", "150", "258", "264", "270"]
vision_goals: [6]
affects:
  - Plan/_planning/charter.md
  - scripts/check-charter-closure
  - tests/test_charter_closure.py
---

# Spec 261 — vision charter: closing audit

## Why

The enhancement charter (Plan/_planning/charter.md) defines a stop
condition: "no existing spec has a remaining enhancement on any of the
five gap axes". Today the charter is prose — readable but not
queryable. This spec ships the STANDING audit that converts the stop
condition into a computed predicate: for each existing spec, derive
which of the five gap axes (token-economy on output side · dogfood
loop · agent-uniform Lifecycle · plugin distribution + first-touch UX
· derivability + drift) have an enhancement shipped; flag any
uncovered cell. The dogfood loop (Spec 150 + 258) then proposes
enhancements for uncovered axes; the live alignment matrix (Spec 191)
tracks progress; Spec 270 verifies the global stop predicate.

## Done When

- [ ] **`scripts/check-charter-closure`** derives the 5-axis × N-spec
      coverage matrix from `Plan/*/spec.md` frontmatter (`enhances:` +
      `vision_goals:`) and renders it as a typed report:
      ```python
      class CharterClosure(TypedDict):
          axes: list[str]                 # 5 named gap axes
          existing_specs: list[str]       # N spec_ids in scope
          coverage: dict[str, dict[str, bool]]  # spec_id -> axis -> covered
          uncovered_cells: list[tuple[str, str]]  # (spec_id, axis)
          closure_pct: float              # 1.0 - uncovered/total
          generated_at: str               # ISO timestamp (in body, NOT prefix)
      ```
- [ ] **A new spec without a Goal-mapping check is rejected** (Spec 149
      drift extension) — `vision_goals: []` or missing trips CI.
- [ ] **The charter's "stop condition" is COMPUTED, not asserted** —
      no hand-written closure percentage anywhere; the matrix renders
      from the live tree on every commit.
- [ ] **CI surfaces the closure status** as a percentage with the
      uncovered cells named — not a binary green/red. Trend over time
      shipped as a graph reflection so regressions are visible.
- [ ] **Measurable invariants** (computed, never pinned):
      - `closure_pct == 1.0 - len(uncovered_cells) / (len(axes) *
        len(existing_specs))` — derived relationship, never a frozen
        number
      - `len(axes) == 5` (the charter's named gap axes) — invariant
        until the charter itself amends
      - every `(spec_id, axis)` pair where the parent's `vision_goals`
        intersects the axis MUST appear in `coverage`
      - `closure_pct` is reported, not asserted — the test gates
        REGRESSIONS (closure should never DROP without a new gap
        legitimately opening)
- [ ] Test: closure matrix correctly identifies uncovered axes on a
      fixture (synthetic spec missing an axis); current live tree
      reports a sensible closure number; sabotaged spec trips the
      regression alarm.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  current Plan/ tree with N=128 existing specs + 5 named axes
When:   scripts/check-charter-closure runs
Then:   produces CharterClosure{axes:[...5...],
        existing_specs:[...128...], closure_pct: 0.71,
        uncovered_cells:[("042","derivability+drift"), ...]}
        AND emits a reflection node "closure_snapshot" with the matrix
        AND CI surfaces "71% closure; 187 cells uncovered" with the
        top-10 uncovered cells named

Given:  a PR adds a new spec without `vision_goals:` in frontmatter
When:   check-charter-closure runs as a pre-merge gate
Then:   exits non-zero with "spec NNN missing vision_goals — closure
        cannot be computed" — the PR cannot merge until the author
        names which Goal(s) the spec serves

Given:  yesterday's closure_pct was 0.71; today's run reports 0.68
When:   the drop is NOT explained by a legitimate new gap (no charter
        amendment in the commit log)
Then:   regression alarm fires; reflection names which cells flipped
        from covered to uncovered (likely a spec was renamed or
        retired without an enhancement re-pointer)
```

## Failure modes (Nygard)

| Failure | Audit response |
|---|---|
| Spec frontmatter malformed (`vision_goals` not a list) | YAML parse error → exit non-zero; cell named in error message |
| Axis-to-Goal mapping drifts from charter text | Doc-drift marker on the charter source flags it via Spec 149 |
| Enhancement spec orphaned (parent retired) | Audit reports orphan; closure NOT credited until reparented |
| New gap axis added mid-flight | Audit recomputes with new denominator; closure_pct legitimately drops; reflection records "axis added" so the drop is explained |
| Self-improvement (Spec 264) proposes enhancement for an uncovered cell | Audit re-runs after merge; cell flips covered; closure_pct climbs; the cycle is observable |

## Interconnects

- Spec 191 (alignment matrix) — the rendered surface that consumes
  this audit's output.
- Spec 149 (derived-doc) — the audit is a derived surface itself.
- Spec 150 (dogfood classifier) — consumes `uncovered_cells` as the
  proposal queue.
- Spec 258 (classifier quality loop) — `closure_pct` is a vital sign
  the loop watches; sudden drops trigger investigation.
- Spec 264 (self-improvement meta-cap) — `develop.self_improve()`
  reads `uncovered_cells` to pick its next target.
- Spec 270 (stop-condition verification) — the global stop predicate
  reduces this matrix to `closure: bool`.
- The charter's measurable closing condition (this + 270 = the
  charter's terminal proof).

## Open questions

1. **Should "existing specs" include the enhancement specs themselves,
   or only the pre-charter spec set?** **Recommend**: only the
   pre-charter set (146 is the first enhancement spec) — measuring
   enhancement coverage of enhancements is circular; Spec 270 handles
   recursive closure separately.
2. **How is an axis "covered" — by depends_on, by enhances, or by
   shipped status?** **Recommend**: by `enhances:` AND
   `status: shipped` — drafts don't count, otherwise opening a draft
   would falsely close the gap.
3. **What's the regression threshold for closure_pct drops?**
   **Recommend**: > 2 percentage points uncxplained — small enough to
   catch drift, large enough to ignore single-spec churn.
