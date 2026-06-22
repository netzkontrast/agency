<!-- agency-node: spec-387 -->
---
spec_id: "387"
slug: loop-activation
status: draft
state: draft
last_updated: 2026-06-21
owner: "@agency"
vision_goals: [1, 2, 4, 5]
depends_on: ["018", "152", "285", "292", "294", "297", "330", "344", "345", "362", "363", "364", "365", "366", "367", "368", "369"]
parent_spec: "362"
affects:
  - agency/capabilities/loop/              # NEW thin capability — the trigger + MCP surface + invocation provenance
  - agency/_loop.py                         # generative advance (ctx.sample), gate enforcement, registry-resolved argv
  - agency/_lifecycle_data/loop/skill.py    # executing wizard phases (invoke/sample/elicit) + per-phase rubric load
  - agency/_lifecycle_data/loop/templates/  # runnable run-loop.py host invoke; real Document emit
domain: loop / lifecycle-spine / provenance
wave: looper-port
---

# Spec 387 — Loop activation (wire the dormant port into a live, provenance-recording runtime)

> Child of Spec 362. The 363–369 port shipped the loop's **primitives** — correct,
> green pure functions — but left them **wired to nothing**: zero production
> callers, no MCP surface, no host sampling, no elicitation, no `Invocation`
> provenance. A **dogfood audit** settled it: `analyze.run` records
> `invocation{capability:"analyze"}` SERVING its intent; the loop's `advance` /
> `compile` / `emit` record **nothing**, because they are module functions called
> with raw pillar handles. The port **bypasses the very provenance moat it claimed
> to light** (Goal 2), is **invisible to the three-verb wire contract** (Goal 5),
> and **never runs a model** though the host advertises `sampling:true,
> elicitation:true`. 387 **activates** the loop without throwing away the tested
> logic: a thin `loop` capability supplies the trigger + MCP surface + invocation
> provenance (Goal 4 — *adding a folder*); `advance` becomes generative via
> `ctx.sample`; the wizard's phases **execute**; emit yields round-trippable
> `Document`s and a runner that actually runs. **The acceptance is the
> dormant-surface audit as a STANDING test** — the gate the original port lacked.

## Why — the gap between "primitives shipped" and "a working loop"

362 was marked **Shipped**. It was not. The 63 green tests assert the **parts in
isolation** (call a function, inspect its return); none exercise a **triggered,
end-to-end, model-driven** loop, so the integration void went unseen. CLAUDE.md's
own **dormant-surface audit** ("count live triggers; zero = dead code") fails for
the entire module. Evidence, all engine-generated:

| Defect (review) | Engine evidence (dogfood) | Goal violated |
|---|---|---|
| Zero production callers | CodeGraph blast radius: every `_loop` fn's callers are `test_loop_*` only | — |
| Bypasses the provenance moat | `analyze.run` → `invocation{capability}`; loop → none; `analyze.paths` = 0 chains | **2** |
| Invisible to the wire contract | no `loop` capability → `search`/`get_schema`/`execute` cannot reach it | **5** |
| No generative core | `grep sample agency/_loop.py` = 0; `doctor.host.sampling = true` (available, unused) | **1** |
| Inert wizard | `LOOP_DESIGN_SKILL` phases have no `invoke=`; walking executes nothing | **1** |
| Decorative gates | `verdict_source_present` is a function the walk never calls | — |
| Non-runnable emit | `compile` emits `host.invoke=["host","-p"]`; the runner would `exec "host"` → rc 127 | **7** |
| Fake round-trip | emitted files carry an anchor comment but bind to **no** `Document` node | **9** |

The lesson (Goal 6): **tests that pin a function's return cannot detect a dead
surface.** 387 fixes the loop AND the test gap — the standing audit (W7) is the
real deliverable.

## The central design decision — a thin `loop` capability (recommended)

362 chose **"spine, not capability."** That was elegant — the loop machine IS a
Lifecycle (Goal 3) — but it **silently traded away** everything the drop-in bar
guarantees: *discoverable, walkable, CLI-exposed, MCP-wired, emittable*, and the
auto-recorded `Invocation`/`Artefact` provenance moat. Nothing replaced it.

**Decision:** keep the spine **logic** (`_loop.py` is tested and good) and add a
**thin `loop` capability** as the missing wired shell. The two are *complementary,
not exclusive*: the capability's verbs are one-line delegations to the existing
`_loop` functions; the loop machine stays on the lifecycle spine. For the cost of
**one folder** (Goal 4) the loop gains: MCP `search`/`get_schema`/`execute`
reachability (Goal 5), a CLI surface, a `/agency-loop` slash, and — because every
capability verb auto-records `Invocation SERVES intent` + `Artefact PRODUCES` —
the **provenance moat for free** (Goal 2).

> **Alternative considered & rejected:** pure spine + bespoke
> invocation-recording + bespoke MCP exposure. Rejected as anti-frugal — it
> rebuilds, by hand, exactly what `CapabilityBase` + `Engine._wire` already
> provide. The interim JSON-on-node stores (criteria/council/progress) likewise
> promote to typed ontology nodes via the capability's `OntologyExtension`.

This **reverses** 362's spine-only framing where it was wrong (the entry surface)
and **preserves** it where it was right (the machine + the pure logic).

## Design (seven workstreams)

### W1 — the `loop` capability: trigger · MCP surface · invocation provenance

`agency/capabilities/loop/` with thin verbs delegating to `_loop`:
`frame_goal · critique_goal · add_criterion · add_member · open · advance ·
verify_report · recommend_council · compile · emit · emit_runner · detect_models ·
register_model · preview`. Each is `@verb(role=…)` returning the `_loop` result, so
discovery (`search "loop"`), schema (`get_schema`), execution (`execute`), the CLI,
and the slash mirror all light up, and each call records an `Invocation` (Goal 2/5).
An `OntologyExtension` promotes the interim JSON stores to typed nodes
(`VerificationCriterion`, `CouncilMember`, `LoopControl`) so the goal→criterion→
verdict→artefact chain is one provenance traversal, and registers the `loop-design`
skill **here** (off `develop`, where it was squatting).

### W2 — generative `advance`: the host actually drafts (`ctx.sample`, Spec 285)

`advance` stops taking `judge_output` as a literal. Instead:
- `planning` / `delivering`: **`ctx.sample(system, prompt)`** has the **host model
  draft** the plan / delivery artefact; the draft is recorded as an **`Artefact`
  PRODUCES** the loop's Intent (Goal 2), then the state moves forward.
- `plan_gate` / `delivery_gate`: run the programmatic criteria (`gate.check`) **and
  convene the council** (`panel.convene` → a real judge verdict via sample/delegate,
  365), feeding `check_criterion`. No host bridge → typed `input-required` (graceful
  degrade, parity with looper's in-session handoff).

The pure `control_evaluate` / `_parse_judge_verdict` stay; W2 only supplies their
inputs from **real model calls** instead of test literals.

### W3 — the executing wizard: phases that DO, rubrics that load

`LOOP_DESIGN_SKILL` phases gain real bodies (Spec 152 phase fields):
- `invoke={capability:"loop", verb:"frame_goal"|"add_criterion"|"open"|"compile"|"emit"}`
  so `develop.skill_walk` **executes** each phase (records an `Invocation` per phase).
- `sample={system, prompt, produces_key}` where the host must draft (host model).
- the **rubric loads at its phase** (progressive disclosure) — the phase surfaces
  `goal-rubric.md` / `verification-rubric.md` / `council-rubric.md` /
  `control-rubric.md` only when entered, never front-loaded.

### W4 — gates that gate

The council & control phases evaluate their **predicate AS the gate**:
`verdict_source_present` (365 reviewer-only rule) and `termination_guard_present`
(366) decide the block — not the walker's generic confirm. A user **cannot**
advance past `council` with no verdict source; the override is recorded as
provenance, never silently allowed.

### W5 — real emit + a runnable runner + TRUE parity

- `emit` renders via **`document.render`** so each file is a `Document` node
  `CONFORMS_TO` the loop schema; an on-disk `loop.yaml` edit round-trips through
  `document.sync` (Goals 7/9) — the net gain over looper, finally real.
- `compile` resolves `host.invoke` and each member's `invoke` from the **model
  registry** (W6), not the `["host","-p"]` placeholder — so the emitted runner
  execs a real CLI.
- `test_loop_roundtrip` **actually runs** the emitted `run-loop.py` against ported
  fake-host / fake-judge / bad-judge fixtures (fake CLIs on `PATH`) and asserts the
  **same gate decisions + same `stop_reason`** as the spine walk. Contract-level
  string matching is replaced by behavioural parity.

### W6 — model-detection parity + the absorbed surface

`detect_models` regains looper's `authed` / `version` / `install` probe fields and
`recommend_council_default` (the privacy-preserving local default, §12). Port
`commands/looper.md` → the `/agency-loop` slash mirror and `agents/openai.yaml` →
seed registry data.

### W7 — the dormant-surface audit as a STANDING acceptance (the real deliverable)

A test that the original port would have **failed**, run in CI forever:
- **reachability:** every `loop` verb is found by `search`, schema'd by
  `get_schema`, and invocable by `execute` (Goal 5).
- **provenance:** after a triggered loop run, `manage.provenance(intent_id)`
  returns an `invocation{capability:"loop"}` chain **plus** the drafted `Artefact`s
  (Goal 2) — the moat lit *the way `analyze` lights it*.
- **liveness:** no `loop` verb has zero reachable callers (CodeGraph blast radius
  asserted, not just tests).

## Acceptance (Gherkin)

```gherkin
Scenario: the loop is reachable through the three-verb wire contract
  When I search the live registry for "loop design an agent loop"
  Then loop verbs (frame_goal, open, advance, compile, emit) are returned
  And get_schema returns their typed schemas
  And execute can invoke loop.frame_goal and get a goal_id back

Scenario: a triggered loop run lights the provenance moat (Goal 2)
  Given a host bridge that can sample
  When I open a loop and advance it through plan_gate and delivery_gate via execute
  Then manage.provenance(intent_id) returns invocation{capability:"loop"} entries
  And the host-drafted plan and delivery artefacts PRODUCE the loop's Intent

Scenario: advance drafts the plan via the host model, not a literal
  Given an open loop and a host sampler
  When I advance from planning
  Then the host is sampled to draft the plan artefact
  And a plan Artefact is recorded before the state reaches plan_gate

Scenario: the council phase blocks until a verdict source exists (W4)
  Given a loop-design walk at the council phase with only reviewer members
  When I try to advance past it
  Then the walk blocks citing the missing verdict_source (not a generic confirm)
  And adding a judge member unblocks it

Scenario: an emitted loop.yaml round-trips through the graph (W5)
  Given an emitted loop.yaml rendered as a Document
  When I edit it on disk and document.sync it
  Then the loop's nodes reflect the edit (keep-both, latest wins)

Scenario: the emitted runner actually runs and agrees with the spine (W5)
  Given ported fake-host and fake-judge CLIs on PATH
  When the same resolved loop runs in-session and via the emitted run-loop.py
  Then both reach the same gate decisions and the same stop_reason

Scenario: the dormant-surface audit fails a verb with no reachable trigger (W7)
  Given a loop verb removed from the capability surface
  When the standing audit runs
  Then it FAILS naming the unreachable verb (the gate the 363-369 port lacked)
```

## Done When

- [ ] `agency/capabilities/loop/` exists; every `_loop` function is a discoverable,
      schema'd, executable, CLI + slash-exposed verb that records an `Invocation`.
- [ ] `advance` drafts plan/delivery via `ctx.sample` and records `Artefact PRODUCES`;
      the council verdict comes from `panel.convene`, not a literal.
- [ ] `loop-design` phases `invoke`/`sample`/`elicit` real verbs; rubrics load per phase;
      the skill is registered on the `loop` capability (off `develop`).
- [ ] council & control gates evaluate their predicates AS the gate (W4).
- [ ] `emit` renders `Document` nodes that `document.sync` round-trips; `compile`
      resolves real argv; `test_loop_roundtrip` executes the runner for true parity.
- [ ] `detect_models` parity (`authed`/`version`/`recommend_council_default`);
      `commands`/`agents` absorbed.
- [ ] **the standing dormant-surface audit** (reachability + provenance + liveness)
      is green in CI — the audit the original port lacked.
- [ ] 362 master + 363–369 Followups corrected to the honest status; `TODO.md` row added.

## Followup — Implementation Status (2026-06-21)

**Verdict:** Partial — **W1 shipped 2026-06-21**; W2–W7 remaining. The
thin-capability direction is taken (reverses 362's spine-only entry surface where
it cost the moat; preserves the spine machine + tested logic). 387 is the
**activation** layer: the thin `loop` capability (done), generative `advance` via
`ctx.sample`, an executing wizard, enforced gates, real Document emit + a runnable
runner with behavioural parity, and the **dormant-surface audit as a standing CI
gate** (its W1 form is live), so "Shipped" can never again outrun "wired."

**W1 — DONE (the loop is reachable + provenance-recording).** `agency/capabilities/loop/`
ships 15 thin verbs delegating to `_loop` (`frame_goal · critique_goal ·
add_criterion · verify_report · add_member · recommend_council · open · advance ·
preview · compile · emit · emit_runner · detect_models · register_model ·
egress_consent`), auto-discovered (drop-in bar). The loop is now found by `search`,
schema'd by `get_schema`, on the CLI (`bin/agency-loop-*`), and **every invocation
records an `Invocation{capability:"loop"}` SERVING the intent** — the moat the
363–369 spine functions bypassed. `tests/acceptance/test_loop_capability.py` is the
dormant-surface audit (reachability + provenance + discovery, 3 scenarios) — it
would have FAILED on the spine-only port. (Intent-id params renamed `goal_id` to
avoid the injected `intent_id` collision.) Interim: ontology stays JSON-on-node;
typed-node promotion is a later slice.

**Blocker / next step:** **W2 — generative `advance`** via `ctx.sample` (the host
drafts plan/delivery as `Artefact PRODUCES`) + council verdict from `panel.convene`,
the slice that makes the loop actually *do* something rather than only move states.
