<!-- doc-source: agency/_loop.py agency/_lifecycle_data/machines.json Plan/362-looper-complete-port/spec.md Plan/387-loop-activation/spec.md -->
# The Loop subsystem — architecture & wiring contract

> **Read this before touching `agency/_loop.py`,
> `agency/_lifecycle_data/loop/`, or a `loop`-named verb/skill/machine.** This is
> the canonical map of the looper port: what it is, how it is *supposed* to run,
> and — load-bearing — **the wiring contract that separates a live loop from a
> dead one.** The 363–369 port shipped correct primitives that were wired to
> nothing; this doc exists so that mistake is never repeated silently. If you add
> loop surface, the **§Wiring contract** invariants are not optional.

> **Status (2026-06-21): PRIMITIVES SHIPPED, NOT YET ACTIVATED.** Specs 363–369
> landed the loop's pure logic (63 green acceptance scenarios). They are **not a
> working loop**: zero production callers, no MCP surface, no host sampling, no
> elicitation, no `Invocation` provenance. **Spec 387 (loop-activation)** wires it.
> Read the [Current state vs target](#current-state-vs-target) table before
> assuming any verb is reachable.

## What the loop is

A native port of **[looper](https://github.com/ksimback/looper)** (Kevin Simback,
MIT) — a loop-design coach + cross-model review council + a small iterate-until-
verified runtime. Ported **onto agency's lifecycle spine**, not as a bespoke
engine: the loop's runtime IS a registered Lifecycle state machine (Spec 345)
walked via the pillar; the loop-specific logic lives in **one module**,
`agency/_loop.py`. MIT attribution travels with the rubrics, the
`loop.yaml`/`run-loop.py` shapes, and the termination model.

> **Spine framing (Spec 362), corrected by 387.** "The loop is a Lifecycle, not a
> capability" is right about the *machine* and the *pure logic* — and **wrong about
> the entry surface**: a non-capability has no MCP reach and records no provenance.
> 387 keeps the spine machine + logic and adds a **thin `loop` capability** as the
> wired shell. Treat "spine" as *where the logic lives*, never as *an excuse to
> skip the wiring contract*.

## The looper → agency mapping

The port's whole thesis: every looper concept already exists as an agency
primitive. Reuse, don't reinvent.

| looper concept | agency primitive | spec |
|---|---|---|
| **goal** (statement + definition-of-done) | an **Intent** (`intent.capture`) decorated with context sources | 363 |
| **verification criteria** (programmatic / judge / human) | typed **gate** criteria → one `GateResult`-shaped verdict | 364 |
| **council** (reviewer / judge, cross-model) | a **persona** (297) bound to a model driver; convene = **panel** (294) | 365 |
| **loop + termination guards** | a registered **Lifecycle machine** `loop` + `control_evaluate` | 366 |
| **7-stage wizard** | a **walkable skill** `loop-design` (`develop.skill_walk`, Spec 018/152) | 367 |
| **loop.yaml / compile / emit** | **Document** + **Schema** + `document.render` (graph → files) | 368 |
| **run-loop.py / model detect / egress** | the out-of-session twin: a stdlib runner + driver registry + a `gate` | 369 |
| **state.json / run-log.md** | **derived from the graph** (`manage.lifecycle` / `lifecycle_trail`) | 366 |

## Components (what exists on disk)

```
agency/_loop.py                      # THE spine module — all loop logic
agency/_lifecycle_data/
  machines.json                      # the `loop` machine (data, Spec 345)
  loop/
    rubrics/                         # goal·verification·council·control·model-detection (vendored verbatim)
    schemas/                         # loop.v1 + loop.resolved.v1 (looper JSON schemas)
    templates/                       # loop.yaml.tmpl, run-loop.py.tmpl (the stdlib external runner)
LOOP_DESIGN_SKILL (in _loop.py)      # the 7-phase wizard, registered into the develop ontology (367)
```

`_loop.py` surface (pure functions today; thin `loop` capability verbs after 387):
`frame_goal` · `critique_goal` · `add_criterion` · `check_criterion` ·
`verify_report` · `add_member` · `recommend_council` · `open_loop` ·
`control_evaluate` · `advance` · `preview` · `compile` · `emit` · `emit_runner` ·
`detect_models` · `register_model` · `egress_consent`.

## The runtime — the lifecycle walk

The `loop` machine (states / transitions in `machines.json`):

```
planning ──▶ plan_gate ──pass──▶ delivering ──▶ delivery_gate ──pass──▶ completed
   ▲            │ revise (revisions++)              │ revise (iterations++)
   └────────────┘            delivering ◀───────────┘
              (any state) ──▶ failed | canceled        terminals: completed·failed·canceled
```

- **`open_loop`** mints `Lifecycle{machine:"loop"}` SERVING the goal Intent and
  records the termination control. **Refuses a guard-free loop** (looper: never
  emit a loop with no termination guard).
- **`advance`** is the sole in-session walk step: read state → run the gate
  (criteria 364 + council verdict 365) → ask `control_evaluate` → `lifecycle.move`
  (the **sole** state writer, Spec 339). pass advances; revise loops back and
  counts; a denied guard fails the loop carrying the `stop_reason`
  (`budget` → `no_progress` → `max_revisions` → `max_iterations`).
- **`control_evaluate`** is pure — ports looper's termination guards. Status &
  `stop_reason` **derive from the graph** (no `state.json` in-session).

**Two surfaces over one resolved contract** (`loop.resolved.json`, 368):
the **in-session spine walk** (canonical in-agency) and looper's **external
`run-loop.py`** (stdlib, reads only the resolved spec). Both honour the same
contract; the spine is the source of truth, the runner is the portable projection.

## Wiring contract (load-bearing — the lesson)

A loop is **dead** unless ALL of these hold. The 363–369 port satisfied *none*;
**Spec 387 makes each a standing acceptance.** When you add loop surface, you
satisfy these or you have shipped dormant code (CLAUDE.md *dormant-surface audit*).

1. **Reach — it MUST be invocable through the wire contract (Goal 5).** Every loop
   verb is discoverable by `search`, schema'd by `get_schema`, and runnable by
   `execute`. A module function nothing calls is invisible; expose it as a `loop`
   **capability** verb (387 W1). *Audit:* `search "loop"` returns the verb;
   CodeGraph blast-radius shows a non-test caller.
2. **Provenance — it MUST record `Invocation`/`Artefact` (Goal 2).** Capability
   verbs auto-record `Invocation SERVES intent` + `Artefact PRODUCES`; **raw pillar
   calls do not.** *Audit:* after a run, `manage.provenance(intent_id)` returns an
   `invocation{capability:"loop"}` chain — *the way `analyze.run` already does.*
   If the loop runs and provenance is empty, the moat is bypassed.
3. **Generative — `advance` MUST draft via `ctx.sample` (Goal 1, Spec 285).** The
   host model drafts the plan/delivery artefact; the council verdict comes from
   `panel.convene`, **not a literal parameter.** The host advertises
   `sampling:true` (`agency doctor`) — use it. A loop that only moves states
   without sampling produces nothing.
4. **Human checkpoints MUST `elicit` (Spec 285).** A `human` criterion / a
   `requires_input` phase pauses for real elicitation, not a docstring.
5. **Gates MUST gate.** The council/control phase predicates
   (`verdict_source_present` 365, `termination_guard_present` 366) decide the
   block — not a generic confirm. An override is recorded as provenance, never
   silently allowed.
6. **Emitted files MUST be `Document`s.** `emit` renders via `document.render` so an
   on-disk `loop.yaml` edit round-trips through `document.sync` (Goals 7/9). A file
   with an anchor *comment* but no `Document` node does **not** round-trip.

## Invariants (safety floor — never cut)

- **Never a guard-free loop** — `open_loop` refuses one with no termination guard.
- **Reviewer-only rule** — a `revise_until_clean` gate REQUIRES a verdict source
  (a judge member or a human criterion); nothing else can declare "clean."
- **argv-only** — every model call / programmatic check / context `cmd` is an argv
  array, never a shell string (Spec 192). No shell interpolation, ever.
- **secret-free** — `detect_models`/`register_model` record argv + family + local
  **only**; never API keys/tokens (auth stays in each CLI's keychain). No secret is
  written into `loop.yaml` / `loop.resolved.json` / the registry.
- **egress consent** — a cross-vendor send requires first-send consent + redaction;
  a `local` member needs none. Consent is recorded as provenance.
- **judge degradation** — unparseable judge output degrades to `revise` + a warning,
  never a crash (`_parse_judge_verdict`).
- **dormant-surface audit** — a declared loop verb/edge that nothing reaches is a
  defect; CI fails on an unreachable verb (387 W7).

## Current state vs target

| Concern | 363–369 (shipped) | 387 (activation) |
|---|---|---|
| Pure logic (guards, taxonomy, compile, egress) | ✅ correct, 63 tests | — keep |
| `loop` machine on the spine | ✅ registered, floor-valid | — keep |
| MCP reach (`search`/`get_schema`/`execute`) | ❌ none | ✅ **W1 done** — thin `loop` capability |
| `Invocation` provenance (every verb) | ❌ bypassed | ✅ **W1 done** — records `Invocation{capability:"loop"}` |
| `Artefact` provenance (host drafts) | ❌ none | ⏳ W2 — `ctx.sample` |
| Generative `advance` (`ctx.sample`) | ❌ literal params | ⏳ W2 — host drafts |
| Executing wizard (phases `invoke`/`sample`) | ❌ inert phases | ✅ real bodies + per-phase rubric |
| Enforced gates | ❌ decorative confirm | ✅ predicate-as-gate |
| Round-trippable emit (`document.render`) | ❌ files + comment | ✅ `Document` nodes |
| Runnable runner + true parity | ❌ placeholder host invoke | ✅ registry argv + subprocess parity |

## Pointers

- **Specs:** [`Plan/362-looper-complete-port`](../../../Plan/362-looper-complete-port/spec.md)
  (master) · 363–369 (children) ·
  [`Plan/387-loop-activation`](../../../Plan/387-loop-activation/spec.md) (the wiring).
- **Code:** `agency/_loop.py` (logic) · `agency/_lifecycle_data/loop/` (data) ·
  `agency/_lifecycle_data/machines.json` (the `loop` machine).
- **Run the audit:** `agency doctor` (host `sampling`/`elicitation`), `analyze.run` /
  `analyze.paths` (provenance contrast), CodeGraph blast-radius (liveness).
