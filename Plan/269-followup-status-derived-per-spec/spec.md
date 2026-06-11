---
spec_id: "269"
slug: followup-status-derived-per-spec
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "149"
depends_on: ["149", "191", "259", "268", "261", "270"]
vision_goals: [4]
affects:
  - scripts/derive-docs
  - Plan/
  - tests/test_followup_derivation.py
---

# Spec 269 — per-spec Followup Implementation Status: derived

## Why

Spec 149 anchors the derived-doc chain (TODO + matrix + SkillDoc).
Per CLAUDE.md rule 4: "Per-spec deep state (test counts, file:line
evidence, verbatim Done / Still / Refinement) lives in each
`Plan/NNN-…/spec.md`'s `## Followup — Implementation Status (…)`
section. No drift between the two; `TODO.md` rolls up, the Followup
section grounds." These sections are hand-authored, drift-prone, and
become stale the moment a test file moves or a commit lands. They
should DERIVE from the same live source as the TODO row: tests
counted from `affects:` plus a grep, Done items mined from
`status: shipped` + commit log, Still items mined from open issues +
remaining unchecked Done-When boxes.

## Done When

- [ ] **`derive-docs` regenerates the `<!-- derived -->` block** of
      the Followup section for every spec with `status` in
      `{partial, shipped}`. Hand-prose lives in
      `<!-- hand -->` blocks and is preserved untouched.
- [ ] **Typed `FollowupBlock` shape**:
      ```python
      class FollowupBlock(TypedDict):
          spec_id: str
          status: Literal["draft","partial","shipped"]
          test_files: list[str]              # from affects: + grep
          test_count: int                    # COMPUTED from collection
          done_when_checked: int             # from spec.md checkbox state
          done_when_total: int               # from spec.md checkbox state
          done_pct: float                    # checked / total
          recent_commits: list[str]          # last N touching affects
          generated_at: str                  # body, not prefix
      ```
- [ ] **Hand-prose preserved** in a manually-edited `<!-- hand -->`
      zone; the `<!-- derived -->` block updates beside it without
      touching hand-prose.
- [ ] **CI fails when derived zones are stale** — derive-docs computes
      the live `FollowupBlock`; if the on-disk derived block diverges
      semantically, CI fails with the diff.
- [ ] **Spec 268 derived fixtures back the test counts** — the
      `test_count` is computed from the LIVE collection, not from a
      hand-pinned number in the spec.
- [ ] **Measurable invariants** (relationships, not pinned counts):
      - `done_pct == done_when_checked / done_when_total` (always
        derived)
      - `done_pct == 1.0 ⇔ status == "shipped"` (status flips when
        all Done-When boxes are checked)
      - `test_count > 0 ⇒ at least one affects: path is a tests/*
        file` (a spec that claims tests must point to test files)
      - `recent_commits` is the LIVE git log filtered by `affects:`
        paths (re-derived each commit; never frozen)
      - re-running derive twice produces identical derived block
        (deterministic; timestamp segregated into body)
- [ ] Test: shipping a fixture spec auto-updates its Followup; manual
      prose unchanged; sabotaged derived block (hand-edit) trips CI
      with the recomputed delta.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  Plan/123-foo/spec.md has affects: ["tests/test_foo.py",
        "agency/capabilities/foo/_main.py"]; checkbox state is 4 of 7
        Done-When boxes checked; status: partial
When:   derive-docs runs
Then:   <!-- derived --> block becomes:
        FollowupBlock{
            spec_id:"123", status:"partial",
            test_files:["tests/test_foo.py"], test_count:11,
            done_when_checked:4, done_when_total:7, done_pct:0.57,
            recent_commits:["a1b2c3 fix foo", "d4e5f6 spec 123"],
        }
        AND <!-- hand --> zone is untouched
        AND TODO.md row for 123 shows "Partial — 4/7" (rolled-up from
        the same source)

Given:  PR changes affects: to include "tests/test_foo_v2.py" and
        adds 3 tests to that file
When:   derive-docs runs as a pre-commit hook
Then:   test_count climbs from 11 → 14; the derived block updates;
        if the commit doesn't update the block, CI fails with the
        recomputed delta

Given:  a malicious PR hand-edits a derived block to claim done_pct=1.0
        without checking the Done-When boxes
When:   CI runs derive-docs in audit mode
Then:   the recomputed block diverges; CI fails; the PR cannot merge
        — the derived source is the ground truth, not the rendered
        block
```

## Failure modes (Nygard)

| Failure | Derivation response |
|---|---|
| `affects:` points to a non-existent path | `Codes.AFFECTS_INVALID`; CI blocks until fixed |
| Test files are derived but contain no tests | `test_count: 0`; flagged in Spec 149 audit |
| Spec has no `<!-- derived -->` block yet (legacy) | First derive run inserts the block above the `<!-- hand -->` zone; subsequent runs maintain it |
| Hand-prose edited into a `<!-- derived -->` block by mistake | CI compares semantic equality (parsed) → diff; fails with location |
| Git history rewrite changes `recent_commits` | Re-derive; the field is live, not pinned |
| Spec marked `shipped` but Done-When not fully checked | Invariant fails: `done_pct == 1.0 ⇔ status == "shipped"`; CI blocks the wrong status |
| Multiple specs share an `affects:` path | Each spec's Followup names the shared path; counts include the full file (relationships, not partitioning) |

## Interconnects

- Spec 149 (parent derived-doc) — this fills the per-spec leaf.
- Spec 191 (matrix) — rolls up `done_pct` across specs.
- Spec 259 (derived-doc self-test) — the self-test covers this
  derivation as one of its surfaces.
- Spec 268 (fixture derivation) — provides the live `test_count`
  source.
- Spec 261 (charter closing audit) — `done_pct` per spec feeds the
  closure matrix.
- Spec 270 (stop-condition) — closure flips on aggregate `done_pct`
  patterns this spec makes computable.
- Closes the CLAUDE.md rule-4 derivation gap.

## Open questions

1. **Should `recent_commits` be a fixed N (default 5) or all-since-
   last-Followup-touch?** **Recommend**: fixed N=5 — bounded size for
   the rendered block; the full log is one `git log` away.
2. **How does the Followup block handle specs in `status: draft`?**
   **Recommend**: render a minimal block (no `recent_commits`, no
   `test_count` if no tests yet) — drafts get a stub so the structure
   is uniform.
3. **Locking — what if two PRs both regenerate Followup blocks in the
   same commit window?** **Recommend**: regeneration is deterministic
   per input; the merge conflict resolves trivially by re-running
   derive-docs post-merge. No special locking.
