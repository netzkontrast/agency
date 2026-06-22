<!-- agency-node: spec-367 -->
---
spec_id: "367"
slug: loop-design-wizard
status: draft
state: done
last_updated: 2026-06-21
owner: "@agency"
vision_goals: [4, 6]
depends_on: ["003", "018", "031", "081", "152", "287", "346", "362", "363", "364", "365", "366", "368"]
parent_spec: "362"
affects:
  - agency/_lifecycle_data/loop/skill.py   # the loop-design phase graph (spine skill data)
  - agency/_lifecycle_data/loop/rubrics/   # the 4 coaching rubrics (loaded per phase)
domain: loop / skills / lifecycle-spine
wave: looper-port
---

# Spec 367 — The loop design wizard (a walkable skill = a skill machine)

> Child of Spec 362. **Spine-framed (2026-06-21):** looper's 7-stage interview is
> a **walkable skill** (`loop-design`), which by Spec 346 *is itself a
> `skill:loop-design` machine on the lifecycle spine*. The wizard is the
> user-facing entry; it **composes the reuse verbs** (intent/gate/panel + the
> pillar + `_loop`) one phase at a time — it adds **no new capability verbs**, only
> the phase graph + the graph-derived preview.

## Why

Looper's `SKILL.md` walks seven stages, **loading each rubric only when its stage
runs** (progressive disclosure) and **critiquing each stage before accepting it**:
goal · verification · host model · council · gates/control · confirmation · emit.

That is *exactly* the agency walkable-skill contract (Spec 081/152): a phase graph
where each phase `produces` keys, optionally `gate`s, and surfaces guidance. And
since Spec 346, a walkable skill **derives a `skill:<name>` machine** and a
`SkillRun` is a lifecycle on it — so the wizard is a spine machine walked via
`develop.skill_walk`, recording a `SkillRun` provenance trail for free.

> Looper's `disable-model-invocation: true` (a deliberate, user-triggered wizard)
> maps to the walkable-skill discipline: walked on request
> (`/agency-loop-design` or `develop.skill_walk`), one phase per turn — never
> auto-fires.

## Design

### The `loop-design` phase graph (spine skill data — no new capability)

Defined with the canonical `phase(index, name, produces, gate=…, verbs=…,
requires_input=…)` helper (`agency/skill.py`), registered as spine skill data
under `agency/_lifecycle_data/loop/` (surfaced through the existing skill
registry; **not** a new `loop` capability). Each phase loads its rubric and
drives the **reuse** verbs from 363–366/368:

```python
SKILL = {"name": "loop-design", "phases": [
  phase(1, "goal",         produces=["goal_id"],   verbs=["intent.capture","intent.confirm"],
        # loads loop/rubrics/goal-rubric.md; advisory clarity gate (363/322)
       ),
  phase(2, "verification", produces=["criteria"],  verbs=["gate.check"],
        gate="has_non_vibe_criterion"     # 364 — warn if all-vibe
       ),
  phase(3, "host",         produces=["host"],      verbs=["persona.create","_loop.detect_models"]),
  phase(4, "council",      produces=["council"],   verbs=["persona.create","panel.convene"],
        gate="verdict_source_present"     # 365 — HARD gate (the reviewer-only rule)
       ),
  phase(5, "control",      produces=["loop_id"],   verbs=["lifecycle.open"],
        gate="termination_guard_present"  # 366 — HARD gate (never a guard-free loop)
       ),
  phase(6, "confirm",      produces=["preview_ok"],verbs=["_loop.preview"],
        requires_input=["preview_ok"]     # human sign-off on the ASCII flow
       ),
  phase(7, "emit",         produces=["emitted"],   verbs=["_loop.compile","_loop.emit"],
        # 368 — write loop.yaml/resolved/LOOP.md/RUN_IN_SESSION.md; offer in-session walk (366)
       ),
]}
```

The skill metadata (`Use when:`/`Triggers:`) **derives** from the spine loop
docstring (derivability audit); only the phase graph is authored.

### Critique-each-stage is a gate, not a vibe

Looper "critiques each stage before accepting it." In agency that critique is the
phase's verb output + an optional `gate`:

- **Advisory phases** (goal, verification) surface findings but the walk proceeds
  — matching looper's "warn, don't block, unless the user explicitly accepts."
- **Hard-gated phases** (council, control) **block advancement**: phase 4 until a
  verdict source exists for every `revise_until_clean` gate (the reviewer-only
  rule, 365); phase 5 until the opened loop has a termination guard (366). These
  are the two invariants looper itself refuses to emit without.

### The ASCII flow preview (phase 6) — generated, not authored

`_loop.preview(loop_id)` renders the terminal-friendly ASCII flow looper shows
before emission — **derived from the `loop` machine (366) + the criteria gates
(364) + the council (365)**, so it can never drift from what will actually run.
Phase 6 `requires_input` holds the walk until the human confirms.

### Slash + discovery surface (Spec 018/025)

The walkable skill auto-exposes `/agency-loop-design` and is found by
`agency search loop` / `mcp__agency__search`. Looper's `commands/looper.md` is
absorbed by this mirror — no hand-written slash file.

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

Scenario: confirmation requires human sign-off on the generated preview
  When I reach the confirm phase
  Then a generated ASCII flow preview is shown and the walk waits for preview_ok

Scenario: walking the skill records a SkillRun provenance trail (a lifecycle on skill:loop-design)
  When I complete the wizard
  Then a SkillRun with seven phase records SERVES the loop's Intent
```

## Done When

- [ ] The `loop-design` walkable skill (7 phases) is registered (spine skill data, not a new cap) and walkable via `develop.skill_walk`; it derives a `skill:loop-design` machine (346).
- [ ] Each phase loads its rubric at its stage (progressive disclosure); rubrics are not front-loaded.
- [ ] Council + control phases hard-gate on the two invariants; goal + verification are advisory.
- [ ] Phase 6 renders a graph-derived ASCII preview and `requires_input` for sign-off.
- [ ] Phase 7 drives `_loop.compile`/`_loop.emit` (368) and offers an in-session machine walk (366).
- [ ] `/agency-loop-design` slash mirror auto-exposed (018); `commands/looper.md` absorbed.
- [ ] `tests/acceptance/test_loop_wizard.py` covers the scenarios.
- [ ] `TODO.md` row updated.

## Followup — Implementation Status (2026-06-21)

**Verdict:** Implemented 2026-06-21 (spine-framed). `LOOP_DESIGN_SKILL` (7 phases,
built with the canonical `phase()` helper) ships in `agency/_loop.py` and is
registered into the **develop** ontology (`develop_ontology.skills["loop-design"]`)
— no new capability — so it walks via `develop.skill_walk` and surfaces in
`agency search` + the regenerated `skills/develop/SKILL.md` install manifest. The
council + control phases are `gate="hard"` (the walker pauses for confirmation);
their SEMANTIC conditions are the predicates `verdict_source_present` (365
reviewer-only rule) and `termination_guard_present` (366 invariant). `_loop.preview`
renders the graph-derived ASCII flow (machine 366 + criteria 364 + council 365)
for phase-6 sign-off. Walking records a `SkillRun` (`Skill` SERVES the Intent + 7
`HAS_PHASE` records) for free. Covered by `tests/acceptance/test_loop_wizard.py`
(6 scenarios green); `test_develop.py` still green (28). **Frugal: net-new is the
phase graph + preview + two predicates — no new capability verbs.**
**Refinement deferred:** auto-evaluating the predicates AS the phase gate (vs. the
walker's generic confirm-pause), and the explicit `skill:loop-design` machine
derivation (346), are follow-ups; the predicates + hard-gate marks carry the
behaviour today.

**Prior draft note:** Re-drafted spine-framed (2026-06-21). Looper's 7-stage interview as
the `loop-design` walkable skill = a `skill:loop-design` machine (346), composing
the **reuse** verbs (intent/gate/persona/panel + the lifecycle pillar + `_loop`)
one phase at a time; rubric progressive disclosure per phase; the two looper
invariants (verdict source, termination guard) as hard phase gates;
graph-derived ASCII preview. **Frugal: no new capability verbs — only the phase
graph + the preview.** Depends on the foundation children + emission (368).
