---
spec_id: "270"
slug: stop-condition-verification
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "_planning/charter"
depends_on: ["261", "264", "150", "191", "258", "269"]
vision_goals: [6]
affects:
  - Plan/_planning/charter.md
  - scripts/check-charter-stop-condition
  - tests/test_stop_condition.py
---

# Spec 270 — charter stop-condition verification

## Why

The charter's stop condition is "the session as a whole stops only
when no existing spec has a remaining enhancement on any of the five
gap axes". Spec 261 audits closure as a matrix; Spec 264 self-improves
toward closure. Neither REDUCES the matrix to the single boolean the
charter actually names. This spec ships THAT predicate — the terminal
proof: `closure: bool` derived from the 5-gap × N-spec coverage
matrix; flips false the moment ANY new spec lacks goal coverage on
any axis it touches. When closure flips true, the wave program is
complete; when it would flip back (a new gap appears, an enhancement
spec is retired without re-coverage), Spec 264 self-improves to close
it. This spec is the ribbon-tie on the entire enhancement charter.

## Done When

- [ ] **`scripts/check-charter-stop-condition`** computes the
      terminal predicate against the live tree:
      ```python
      class StopCondition(TypedDict):
          closure: bool                    # the terminal predicate
          axes_total: int                  # 5
          existing_specs_total: int        # N
          covered_cells: int               # 0..(5*N)
          uncovered_cells: list[CellRef]   # [{spec_id, axis, reason}]
          first_uncovered: CellRef | None  # the one to close next
          rationale: str                   # plain-English why closure is/isn't
          measured_at: str                 # body, not prefix
      ```
- [ ] **Predicate definition is EXACT** and grounded in the closure
      matrix:
      ```
      closure := for every existing spec S and every axis A in S.vision_goals:
                exists enhancement spec E such that
                  E.enhances == S.id AND
                  E.status == "shipped" AND
                  E.vision_goals ⊇ {A}
      ```
      Any failure of the predicate names the (spec_id, axis) pair.
- [ ] **Public closure status** rendered in the alignment matrix
      (Spec 191) — not just "5/5 axes covered for X of Y existing
      specs" but the boolean itself, with the first uncovered cell
      named so the next session has a target.
- [ ] **Self-test** — flip a gap-axis coverage off in a fixture (e.g.
      retire an enhancement spec), assert the stop predicate returns
      false with the right gap named in `first_uncovered`.
- [ ] **CI surfaces closure trend** over time — `closure_pct` history
      lives as graph reflections; a regression alarm fires when the
      pct drops without an explanatory commit (new gap, retired spec).
- [ ] **Measurable invariants** (ALL derived, ZERO pinned):
      - `closure == True ⇔ len(uncovered_cells) == 0` (defining
        biconditional)
      - `covered_cells + len(uncovered_cells) <=
        axes_total * existing_specs_total` (cardinality bound;
        equality when every (S, axis) pair is in scope)
      - `first_uncovered is None ⇔ closure == True` (UX invariant —
        when closed, there's nothing to name)
      - `closure == False AND no commit since last True ⇒ regression
        alarm` (drift detection)
      - the predicate's evaluation is DETERMINISTIC per repo state
        (running twice produces identical `closure` + same
        `uncovered_cells`)
- [ ] Test: predicate correct on current state (computed value
      reported, not asserted to a specific bool); on synthetic
      regressions (fixture removes a covering spec) it flips false
      with the right cell named; on synthetic closure (fixture adds
      every missing cell) it flips true.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  current tree — 128 existing specs, 5 axes, 537 covered cells,
        103 uncovered cells (some specs don't touch all 5 axes; only
        applicable axes are in scope)
When:   scripts/check-charter-stop-condition runs
Then:   StopCondition{
            closure:False,
            axes_total:5, existing_specs_total:128,
            covered_cells:537,
            uncovered_cells:[{spec_id:"042",
                axis:"derivability+drift",
                reason:"no enhancement spec with E.enhances=='042'
                       AND status:'shipped' AND axis in vision_goals"},
                ...],
            first_uncovered:{spec_id:"042", axis:"derivability+drift"},
            rationale:"103 of 640 in-scope (S,axis) cells uncovered;
                       see first_uncovered for next target"
        }
        AND closure_pct = 537 / 640 = 0.84 emitted to the matrix

Given:  closure reached (uncovered_cells == []) and an OLD enhancement
        spec is retired without re-pointer
When:   the next check-charter-stop-condition runs
Then:   closure flips False; first_uncovered names the newly-orphaned
        cell; reflection records "closure regression: spec NNN
        retired without re-coverage"
        AND Spec 264 self-improvement picks up the orphan as its
        next chosen_gap

Given:  closure was True yesterday; today, no spec retirements + no
        new uncovered cells; closure flips False anyway
When:   regression alarm fires
Then:   the predicate's determinism invariant is violated → audit fails
        with "non-deterministic stop predicate" (a real bug to fix;
        the predicate is supposed to be a pure function of repo state)
```

## Failure modes (Nygard)

| Failure | Predicate response |
|---|---|
| Spec frontmatter missing `vision_goals` | Spec 261 already blocks; this spec inherits — closure cannot be computed for that spec |
| Enhancement spec's `enhances:` points to non-existent parent | `uncovered_cells` lists the orphan; rationale names "orphaned enhancement" |
| Charter amendment ADDS a new axis | `axes_total` climbs; closure legitimately drops; reflection records "axis added" so the drop is explained |
| Enhancement spec status flips `shipped → partial` (regression) | covered_cells drops; closure may flip; the cell name guides recovery |
| Non-determinism in the predicate evaluation | Invariant 5 trips; this is a CODE bug in the audit, not a config issue |
| Charter file moved or renamed | The script's `<!-- doc-source: -->` marker (Spec 149) flags it; the predicate is unable to compute until the charter resolves |
| Two enhancement specs both claim the same cell | Idempotent — duplicates don't double-count; both are recorded as covering the cell |
| Closure flips True for the first time | A celebration reflection emits; Spec 264's chosen_gap returns None until a regression |

## Interconnects

- Spec 261 (closing audit matrix) — this spec reduces 261's matrix
  to the terminal boolean.
- Spec 264 (self-improvement) — consumes `first_uncovered` as the
  next-action signal; their loop is the operational drive to flip
  closure True.
- Spec 150 (dogfood classifier) — proposals route toward
  `first_uncovered`.
- Spec 191 (matrix) — the rendered surface where closure status
  lives.
- Spec 258 (classifier quality loop) — `closure` is one of the loop's
  vital signs.
- Spec 269 (per-spec Followup derived) — `done_pct` per spec is one
  input to the closure determination (a `partial` enhancement
  doesn't fully cover its cell).
- The charter's terminal proof.

## Open questions

1. **Should `closure` require ALL Done-When boxes checked across every
   enhancement spec, or just `status: shipped`?** **Recommend**:
   `status: shipped` is the signal; the status flip already requires
   all Done-Whens (per Spec 269 invariant 2). Double-counting is
   redundant.
2. **What about axes a spec doesn't touch — are they "covered" by
   default?** **Recommend**: out-of-scope, not covered. A spec's
   `vision_goals` defines the in-scope axes; only those count toward
   that spec's coverage.
3. **How is closure communicated to a session at start?**
   **Recommend**: Spec 176 sessionstart capture reads the predicate;
   when closure is False, the session-start brief names
   `first_uncovered` so the agent has an immediate next-target.
