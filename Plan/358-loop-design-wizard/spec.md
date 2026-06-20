---
spec_id: "358"
slug: loop-design-wizard
status: draft
last_updated: 2026-06-20
owner: "@agency"
vision_goals: [4, 6]
depends_on: ["003", "018", "031", "081", "152", "287", "346", "353", "354", "355", "356", "357", "359"]
parent_spec: "353"
domain: loop / skills
wave: looper-port
---

# Spec 358 — The loop design wizard (a walkable skill)

> Child of Spec 353. Ports looper's **`SKILL.md` 7-stage interview** and the
> `/looper` command. This is the user-facing entry to the whole cluster. Looper's
> wizard IS a Lifecycle template; agency runs it as a **walkable skill**
> (`SkillRun` phase-graph, `develop.skill_walk`) so the engine delivers ONE phase
> at a time and records a `SkillRun` provenance trail.

## Why

Looper's `SKILL.md` walks seven stages, **loading each rubric only when its stage
runs** (progressive disclosure) and **critiquing each stage before accepting it**:

1. **goal** (`goal-rubric.md`) — coach outcome/scope/context/done
2. **verification** (`verification-rubric.md`) — push toward programmatic
3. **host model** — pick the model that drives the loop
4. **council** (`council-rubric.md`) — add reviewer/judge, recommend a different family
5. **gates & control** (`control-rubric.md`) — revision/iteration/no-progress/budget caps, human checkpoints, execution boundary, isolation
6. **confirmation** — render an ASCII flow preview, get sign-off
7. **emit / run** — write the artefacts; offer to run in-session

This is *exactly* the agency walkable-skill contract (Spec 081): a phase-graph
where each phase `produces` keys, optionally `gate`s, and surfaces guidance. 358
defines the `loop-design` skill whose seven phases each delegate to a sibling verb
from 354–357/359 and load that stage's rubric.

> Looper's `disable-model-invocation: true` (a deliberate, user-triggered wizard
> that writes files) maps to agency's walkable-skill discipline: the skill is
> walked on request (`/agency-loop-design` or `develop.skill_walk`), advancing one
> phase per turn — it never auto-fires.

## Design

### The `loop-design` phase-graph

Built with the canonical `phase(index, name, produces, gate=…, verbs=…,
requires_input=…)` helper (`agency/skill.py`) the `SkillRun` walker consumes
(Spec 152/346). Each phase names the rubric it loads and the verb it drives:

```python
SKILL = {
  "name": "loop-design",
  "phases": [
    phase(1, "goal",        produces=["goal_id"],        verbs=["loop.frame_goal","loop.critique_goal"],
          # loads data/rubrics/goal-rubric.md; gate: clarity advisory (354)
         ),
    phase(2, "verification", produces=["criteria"],       verbs=["loop.add_criterion","loop.verify_report"],
          gate="has_non_vibe_criterion"   # 355 — warn if all-vibe, hard-gate only on explicit accept
         ),
    phase(3, "host",         produces=["host_member"],    verbs=["loop.add_member","loop.detect_models"],
          # which model drives the loop (356/360)
         ),
    phase(4, "council",      produces=["council"],        verbs=["loop.add_member","loop.recommend_council"],
          gate="verdict_source_present"   # 356 — HARD gate (the reviewer-only rule)
         ),
    phase(5, "control",      produces=["control"],        verbs=["loop.open_loop"],
          gate="termination_guard_present"  # 357 — HARD gate (never a guard-free loop)
         ),
    phase(6, "confirm",      produces=["preview_ok"],     verbs=["loop.preview"],
          requires_input=["preview_ok"]   # human sign-off on the ASCII flow
         ),
    phase(7, "emit",         produces=["emitted"],        verbs=["loop.compile","loop.emit","loop.render_handoff"],
          # 359 — write loop.yaml/resolved/LOOP.md/RUN_IN_SESSION.md; offer in-session run (357)
         ),
  ],
}
```

The skill is **derived from the cap docstring** where possible (derivability
audit, `CLAUDE.md`) — `Use when:` / `Triggers:` come from the `loop` module
docstring; only the phase graph is authored.

### Critique-each-stage is a gate, not a vibe

Looper "critiques each stage before accepting it." In agency that critique is the
phase's verb output + an optional `gate`:

- **Advisory phases** (goal, verification) surface findings (354 `critique_goal`,
  355 `verify_report`) but the walker proceeds — matching looper's "warn, don't
  block, unless the user explicitly accepts the risk."
- **Hard-gated phases** (council, control) **block advancement**: phase 4 will not
  pass until `recommend_council` reports a verdict source for every
  `revise_until_clean` gate (the reviewer-only rule, 356); phase 5 will not pass
  until `open_loop` accepts a termination-guarded control (357). These are the two
  invariants looper itself refuses to emit without.

### The ASCII flow preview (phase 6)

`loop.preview(loop_id)` renders the loop as the terminal-friendly ASCII flow
looper shows before emission — derived from the machine (357) + gates (355) +
council (356), optimized for Claude Code CLI width:

```text
+--------------------------------+
| 1. Goal + context              |
+--------------------------------+ -> 2. plan.md -> {plan gate: judge reviewer-1}
   revise <= 3 -^                                       | pass
                                                        v
                          4. delivery-N -> {delivery gate} -> 6. done (all gates clean)
   revise <= 3 -^
Stops: pass gates | max 12 iterations | no progress x2 | budget 30m, $5.0
```

The preview is **generated, not authored** (it reads the graph), so it can never
drift from what will actually run. Phase 6 `requires_input` holds the walk until
the human confirms.

### Slash + discovery surface (Spec 018 / 025)

The walkable skill auto-exposes `/agency-loop-design` (Spec 018 win) and is found
by `python -m agency.cli search loop` / `mcp__agency__search`. Looper's
`commands/looper.md` is absorbed by this mirror — no hand-written slash file.

## Acceptance (Gherkin)

```gherkin
Scenario: the wizard delivers one phase at a time
  When I walk the loop-design skill
  Then the engine returns phase 1 (goal) only, with its rubric loaded
  And advancing returns phase 2 (verification), not the whole graph

Scenario: each stage loads its own rubric (progressive disclosure)
  When I reach the council phase
  Then council-rubric.md is surfaced and goal-rubric.md is not re-sent

Scenario: the council phase hard-gates on the reviewer-only rule
  Given a revise_until_clean gate with only reviewer members
  When I try to advance past the council phase
  Then the walk blocks until a judge member or human verdict source is added

Scenario: the control phase hard-gates on a termination guard
  Given a control with no caps
  When I try to advance past the control phase
  Then the walk blocks until at least one termination guard is set

Scenario: the goal phase warns but does not block
  Given a weak goal
  When I advance past the goal phase having acknowledged the warning
  Then the walk proceeds (advisory parity)

Scenario: confirmation requires human sign-off on the generated preview
  When I reach the confirm phase
  Then a generated ASCII flow preview is shown and the walk waits for preview_ok

Scenario: emit produces the artefacts and offers an in-session run
  When I complete the emit phase
  Then loop.yaml, loop.resolved.json, LOOP.md, and RUN_IN_SESSION.md exist (359)
  And the wizard offers to advance the loop machine in-session (357)

Scenario: walking the skill records a SkillRun provenance trail
  When I complete the wizard
  Then a SkillRun with seven phase records SERVES the loop's Intent
```

## Done When

- [ ] The `loop-design` walkable skill (7 phases) is registered on the cap ontology and walkable via `develop.skill_walk`.
- [ ] Each phase loads its rubric at its stage (progressive disclosure); rubrics are not front-loaded.
- [ ] Council + control phases hard-gate on the two invariants (verdict source; termination guard); goal + verification are advisory.
- [ ] Phase 6 renders a graph-derived ASCII preview and `requires_input` for sign-off.
- [ ] Phase 7 drives `compile`/`emit`/`render_handoff` (359) and offers an in-session machine walk (357).
- [ ] `/agency-loop-design` slash mirror auto-exposed (Spec 018); `commands/looper.md` absorbed.
- [ ] Walking records a `SkillRun` trail; `tests/acceptance/test_loop_wizard.py` covers the scenarios.
- [ ] `TODO.md` row updated.

## Followup — Implementation Status (2026-06-20)

**Verdict:** Not started — drafted under the 353 wave. Looper's 7-stage interview
as a `loop-design` walkable skill (`SkillRun`, 346) composing 354–357/359; rubric
progressive disclosure per phase; the two looper invariants (verdict source,
termination guard) enforced as hard phase gates; graph-derived ASCII preview.
Depends on all four foundation children + emission (359); the user-facing entry
to the cluster.
