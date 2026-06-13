# Phase C — Test restructure + contract gating (reviewer-owned)

> Vision-program Phase C. Brought forward by owner directive (2026-06-13): the
> Review-partner session now **owns tests**, GitHub CI is **disabled**, and tests
> are written as **contracts derived from the Vision + the refactor agent's
> PROPOSALS** (`refactor.md` / PR comments) — **never from reading his code**.

## Two jobs

### 1. Contract / acceptance gating (the new CI)
`tests/contract/` holds **invariant tests** that encode what the four-pillar
OOP refactor MUST satisfy — derived from `docs/vision/CORE.md` §"Four complete
pillars" + the agent's stated seam contracts. Two kinds:
- **Behaviour-preserving guards** (GREEN today; must stay green): the wire
  contract is exactly `{search, get_schema, execute}`; live verb count stable;
  `agency_doctor` field-set stable; MCP≡bash isomorphism.
- **Refactor targets** (RED today, `xfail(strict=True)` → flip loudly when met):
  the A1 read-pillar invariant (no raw `.g` in `capabilities/`); capability-
  per-folder (Goal 4); each pillar's surface cleanly separated.

**Gating model:** CI is off. I run `tests/contract/` against the agent's branch
state (running ≠ reading) and report pass/fail on the PR thread. A refactor
slice is "done" when its target test flips GREEN without regressing a guard.

### 2. Restructure the 193 flat test files onto the four pillars
`tests/test_*.py` (193, auto-markered by filename prefix in `conftest.py`
`_AUTO_MARKER_PATTERNS`) → organized by pillar + capability:
```
tests/
  contract/        # the acceptance/invariant suite (new; the gate)
  intent/          # intent · thinking · dogfood
  capability/      # plugin · skill_generator · skills · document · prompt · analyze · music · novel
  lifecycle/       # develop · gate · delegate · subagent · jules · workspace · branch
  memory/          # reflect · research · management(290)
  substrate/       # engine · memory-store · ontology · skill · toolresult · cli · install
```
Moves preserve `conftest.py` marker behaviour (update `_AUTO_MARKER_PATTERNS`
to the new layout). Restructuring test files is reading TESTS, not his impl —
within the constraint.

## Constraint: proposals, not code
- Reviews read `refactor.md` + PR comments; **never `git show` his diffs**.
- Contract tests target the **public API + the proposed invariants**, computed
  from the live tree/registry (rule 8 — relationships, not frozen snapshots).
- I may **run** tests against his branch (black-box pass/fail); I do not read
  the implementation to write or debug them — if a test is ambiguous, I refine
  the *contract* with him on the thread.

## Acceptance (the standing /goal)
The refactor is "done" (per the goal) when, on the agent's branch:
- every `tests/contract/` target invariant is GREEN (four-pillar separation +
  capability-per-folder + no raw graph access), and
- every behaviour-preserving guard is still GREEN (zero contract/wire/verb-name
  drift), and
- the full restructured suite passes.
Then Phases A/B/C merge in order; CI workflow is re-enabled (rename back).

## Sequencing
Contract tests land first (define the target). The flat-test restructure
proceeds in parallel but does NOT gate the refactor (it's organization). The
`/plans` migration + Spec 290 build remain out of scope.
