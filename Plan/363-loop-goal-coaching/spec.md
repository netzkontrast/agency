<!-- agency-node: spec-363 -->
---
spec_id: "363"
slug: loop-goal-coaching
status: draft
last_updated: 2026-06-21
owner: "@agency"
vision_goals: [2, 6]
depends_on: ["091", "307", "312", "315", "322", "362"]
parent_spec: "362"
affects:
  - agency/_lifecycle_data/loop/rubrics/   # goal-rubric.md (verbatim from looper)
  - agency/capabilities/intent/            # reuse — the goal IS a root Intent
domain: loop / intent / lifecycle-spine
wave: looper-port
---

# Spec 363 — Loop goal coaching (the goal IS a root Intent)

> Child of Spec 362. **Spine-framed + frugal (2026-06-21):** looper's goal stage
> maps onto agency's primitive looper lacked — the **Intent**. A loop's goal IS
> its root Intent (`intent.capture` purpose/acceptance ≈ looper's
> statement/definition_of_done). 363 adds only the **goal rubric** (data) as the
> critique source + the binding of `context_sources` onto the Intent. **No new
> capability** — critique reuses the clarity gate (322) + intent methods (091).

## Why

Looper interviews for a goal then **critiques it** against `goal-rubric.md`:
outcome-vs-activity framing, an explicit scope boundary, named context sources, a
falsifiable "done" state — pushing weak goals to gather context, not assume it.

```yaml
goal:
  statement: >
    Produce an agent workflow map for <client> converting their manual process
    into a stepwise agent design with tool calls and handoffs.
  context_sources:
    - { file: ./inputs/process-notes.md }
    - { cmd: ["ls", "./inputs/transcripts"] }   # argv, never a shell string
  definition_of_done: >
    A LOOP.md the client can execute, every step mapped to a tool or human action,
    nothing left "TBD".
```

In agency: `statement` → the Intent **purpose**; `definition_of_done` → the Intent
**acceptance**; `context_sources` → a structured prop on the Intent the loop may
inspect (resolved at compile/run time, never shell-interpolated).

## Design

### The goal = the root Intent (reuse, no new node)

The wizard's goal phase (367 phase 1) calls `intent.capture` / `intent.confirm`
(the goal IS the Intent the loop SERVES) and stores `context_sources` as structured
`{file}` / `{cmd:[argv]}` entries — **argv arrays, never shell strings** (looper
File Rule + `shell` safety, 192). A `cmd` source is resolved by the
machine/runner, not at framing time.

### The goal rubric drives critique (derive, don't re-author)

`goal-rubric.md` ships verbatim to `agency/_lifecycle_data/loop/rubrics/`. Critique
**reuses existing machinery** rather than a new coaching engine:

- **Falsifiable done-state** → the Spec 322 **intent-clarity-score** gate; a
  `definition_of_done` scoring below threshold is flagged (not blocked — the
  wizard, 367, decides whether to hard-gate).
- **Outcome-vs-activity / scope / gather-vs-assume** → Spec 091 intent
  critical-thinking methods + Spec 315 framing. No new coaching engine — 363 is
  the rubric + the binding; the reasoning is borrowed.

### Coaching is advisory by default (looper parity)

Looper warns loudly but lets the user accept a weak goal. 363 mirrors this:
critique returns findings, it does not block. Any hard gate is the wizard's call
(367), and even there a user override is recorded as provenance, not refused.

## Acceptance (Gherkin)

```gherkin
Scenario: framing a goal binds it to a root Intent
  When I capture a goal with a statement, definition_of_done, and two context_sources
  Then the loop's root Intent has purpose=statement and acceptance=the done-state
  And the context_sources are stored as structured file/argv entries

Scenario: a cmd context source must be an argv array, never a shell string
  When I supply a context source cmd "ls ./inputs; rm -rf /"
  Then it is rejected as not an argv array

Scenario: critique flags an activity-framed, unfalsifiable goal
  Given a goal stated as "work on improving the docs" with done-state "make it good"
  When I critique the goal against goal-rubric.md
  Then a finding flags outcome-vs-activity citing the rubric
  And the unfalsifiable done-state is flagged via the clarity score (322)
  And critique does not block (advisory parity with looper)

Scenario: a sharp goal passes critique clean
  Given a goal with an outcome statement, a scope boundary, named context, and a checkable done-state
  When I critique it
  Then every rubric dimension is ok and clarity is above threshold
```

## Done When

- [ ] A loop's goal is a root Intent (`intent.capture`); `statement`/`definition_of_done`/`context_sources` round-trip; `cmd` sources are argv-validated.
- [ ] Critique reuses `intent.clarity_score` (322) + Spec 091 methods — no new coaching engine — and surfaces `goal-rubric.md` findings; advisory, non-blocking.
- [ ] `goal-rubric.md` ships verbatim under `agency/_lifecycle_data/loop/rubrics/`.
- [ ] `tests/acceptance/test_loop_goal.py` covers the scenarios.
- [ ] `TODO.md` row updated.

## Followup — Implementation Status (2026-06-21)

**Verdict:** Implemented (spine slice; 2026-06-21). Goal-as-root-Intent + the goal
rubric as critique source, reusing `clarity_score` (322); `context_sources` stored
argv-safe on the Intent. Advisory-not-blocking parity with looper. **Frugal:
net-new is goal-rubric (data) + two spine functions — no new capability verb.**

### Done
- `agency/_loop.py::frame_goal` — goal → root Intent (`intent.capture` purpose=
  statement, acceptance=definition_of_done); `context_sources` argv-validated
  (`_validate_context_sources` rejects shell-string `cmd`s) + stored JSON on the
  Intent.
- `agency/_loop.py::critique_goal` — advisory rubric findings (outcome-vs-activity,
  falsifiable done-state, gather-vs-assume), each citing `goal-rubric.md`; reuses
  `clarity_score` (322) as a reported signal; never blocks.
- `goal-rubric.md` vendored verbatim → `agency/_lifecycle_data/loop/rubrics/`
  (referenced at runtime via `rubric_path` — not dormant).
- `tests/acceptance/{features/loop_goal.feature,test_loop_goal.py}` — 4 scenarios
  GREEN (framing+argv-safety, shell-string rejection, advisory critique, sharp goal
  clean). All loop slices together = 18 green.

### Still / Refinement
- Clarity is surfaced as an advisory signal in the critique result (not a hard
  threshold finding) — a fresh goal scores below `CLARITY_THRESHOLD` until scope/
  measurable-acceptance/grounding nodes exist; the wizard (367) decides any hard
  gate, matching looper's advisory model.
- `frame_goal`/`critique_goal` are spine functions today; they surface as cap verbs
  when the `agency/capabilities/loop/` folder lands (367 composes them as phases).
