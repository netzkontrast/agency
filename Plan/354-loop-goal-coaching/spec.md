---
spec_id: "354"
slug: loop-goal-coaching
status: draft
last_updated: 2026-06-20
owner: "@agency"
vision_goals: [2, 6]
depends_on: ["091", "307", "312", "315", "322", "353"]
parent_spec: "353"
domain: loop / intent
wave: looper-port
---

# Spec 354 — Loop goal coaching (the goal becomes an Intent)

> Child of Spec 353 (looper-complete-port). Ports looper's **goal stage** +
> `references/goal-rubric.md`. The wedge looper opens here: *"Garbage goal in,
> confidently-wrong loop out."* Agency already has the primitive looper lacked —
> the **Intent** — plus a clarity gate (Spec 322) and critical-thinking methods
> (Spec 091). 354 wires the goal rubric onto them.

## Why

Looper's first stage interviews the user for a goal, then **critiques it** against
`goal-rubric.md`: outcome-vs-activity framing, an explicit scope boundary, named
context sources, and a falsifiable "done" state — pushing weak goals to gather
context instead of assuming it. The `loop.yaml` `goal` block is the encoded
result:

```yaml
goal:
  statement: >
    Produce an agent workflow map for <client> that converts their manual
    process into a stepwise agent design with tool calls and handoffs.
  context_sources:
    - file: ./inputs/process-notes.md
    - cmd: ["ls", "./inputs/transcripts"]
  definition_of_done: >
    A LOOP.md the client can execute, every step mapped to a tool or human
    action, nothing left "TBD".
```

In agency, **a loop's goal IS the loop's root Intent.** `intent_bootstrap` already
takes `purpose` / `deliverable` / `acceptance` — a near-exact match for
looper's `statement` / (implicit output) / `definition_of_done`. The
contribution of 354 is (a) the **goal rubric** as the critique source, and (b)
binding `context_sources` and `definition_of_done` onto the Intent so the loop
machine (357) and the council (356) can read them.

## Design

### `LoopGoal` wraps the root Intent

The goal does not duplicate the Intent — it **decorates** it. `frame_goal` calls
`intent_bootstrap` (or adopts the active intent) and attaches the loop-specific
fields:

```python
@verb(role="effect")
def frame_goal(self, ctx, statement: str, definition_of_done: str,
               context_sources: list[dict] | None = None) -> dict:
    """Bind a loop's goal to its root Intent (the loop SERVES this intent).

    `statement` → the Intent purpose; `definition_of_done` → the Intent
    acceptance criterion; `context_sources` → [{file:…}|{cmd:[argv]}] the
    loop may inspect (resolved at compile/run time, never shell-interpolated).

    Returns: {goal_id, intent_id, clarity}. chain_next: loop.critique_goal to
    coach it, then loop.add_criterion (355).
    """
```

`context_sources` is stored as structured `{file}` / `{cmd: [argv]}` entries —
**argv arrays, never shell strings** (looper File Rule + agency `shell` safety,
Spec 192). A `cmd` source is resolved by the runner/machine, not at framing time.

### The goal rubric drives critique (derive, don't re-author)

`references/goal-rubric.md` ships verbatim to
`agency/capabilities/loop/data/rubrics/goal-rubric.md`. `critique_goal` surfaces it
as the system frame for a critique pass and reuses existing intent machinery
rather than re-implementing coaching:

```python
@verb(role="transform")
def critique_goal(self, ctx, goal_id: str) -> dict:
    """Coach a loop goal against goal-rubric.md. Returns typed findings:
    outcome-vs-activity, scope boundary present?, context gathered-vs-assumed,
    falsifiable done-state? Each finding cites the rubric line.

    Reuses intent.clarity_score (Spec 322) for the falsifiability signal and
    intent critical-thinking (Spec 091) for the framing critique. Returns
    {findings: [{dimension, verdict, rubric_ref, suggestion}], clarity}.
    chain_next: re-frame_goal on a failing dimension, or proceed to 355.
    """
```

- **Falsifiable done-state** maps to the **Spec 322 intent-clarity-score gate** —
  reuse it; a goal whose `definition_of_done` scores below threshold is flagged
  (not blocked — the wizard, 358, decides whether to hard-gate).
- **Outcome vs activity / scope / gather-vs-assume** reuse **Spec 091** intent
  critical-thinking methods + **Spec 315** framing frameworks. No new coaching
  engine — 354 is the rubric + the binding, the reasoning is borrowed.

### Coaching is advisory by default (looper parity)

Looper warns loudly but lets the user accept a weak goal ("unless the user
explicitly accepts that risk"). 354 mirrors this: `critique_goal` returns findings;
it does not block. The hard gate (if any) is the wizard's call (358), and even
there a user override is recorded as provenance, not refused.

## Acceptance (Gherkin)

```gherkin
Scenario: framing a goal binds it to a root Intent
  When I frame_goal with a statement, definition_of_done, and two context_sources
  Then a LoopGoal is recorded that decorates an Intent
  And the Intent purpose equals the statement and its acceptance equals the done-state
  And the context_sources are stored as structured file/argv entries

Scenario: a cmd context source must be an argv array, never a shell string
  When I frame_goal with a context source cmd "ls ./inputs; rm -rf /"
  Then framing rejects it as not an argv array

Scenario: critique flags an activity-framed, unfalsifiable goal
  Given a goal stated as "work on improving the docs" with done-state "make it good"
  When I critique_goal
  Then a finding flags outcome-vs-activity citing goal-rubric.md
  And a finding flags the unfalsifiable done-state via the clarity score
  And critique does not block (advisory parity with looper)

Scenario: a sharp goal passes critique clean
  Given a goal with an outcome statement, a scope boundary, named context, and a checkable done-state
  When I critique_goal
  Then every rubric dimension verdict is "ok" and clarity is above threshold
```

## Done When

- [ ] `loop.frame_goal` records a `LoopGoal` decorating an Intent; round-trips
      `statement`/`definition_of_done`/`context_sources`.
- [ ] `cmd` context sources are argv-validated (reject shell strings).
- [ ] `loop.critique_goal` returns rubric-cited findings, reusing
      `intent.clarity_score` (322) and Spec 091 methods — no new coaching engine.
- [ ] `goal-rubric.md` ships verbatim under `data/rubrics/`.
- [ ] `tests/acceptance/test_loop_goal.py` covers the scenarios above.
- [ ] `TODO.md` row updated.

## Followup — Implementation Status (2026-06-20)

**Verdict:** Not started — drafted under the 353 wave. Goal-as-Intent binding +
the goal rubric as critique source, reusing the clarity gate (322) and intent
critical-thinking (091). Advisory-not-blocking parity with looper. Foundation
sibling to 355/356/357; consumed by the wizard (358).
