<!-- agency-node: spec-362 -->
---
spec_id: "362"
slug: looper-complete-port
status: draft
last_updated: 2026-06-21
owner: "@agency"
vision_goals: [1, 2, 3, 4, 6]
depends_on: ["003", "040", "043", "091", "179", "192", "283", "285", "292", "294", "297", "322", "328", "334", "338", "339", "340", "344", "345", "346", "349"]
affects:
  - agency/_lifecycle_data/machines.json   # the "loop" machine (data, the 345 seam)
  - agency/_loop.py                          # the one spine module (walk reducer + control + compile/emit + models)
  - agency/_lifecycle_data/loop/             # rubrics + templates + schemas + example + the loop-design skill (data)
source-repos:
  - "looper @ netzkontrast/looper (Kevin Simback / @ksimback, MIT) — SKILL.md 7-stage wizard, scripts/looper.py, templates/run-loop.py, 2 JSON schemas, 4 rubrics + model-detection, templates, ai-workflow-mapping example"
domain: loop / lifecycle-spine
wave: looper-port
---

# Spec 362 — Looper port = the lifecycle spine (master)

> **Master spec** — coordinates children 363–369. **Reframed 2026-06-21 (owner):
> the looper port is the lifecycle SPINE, not a `capabilities/loop/` capability.**
> Lifecycle is the system's **state machine + event bus** (Spec 339/345 + 349b),
> wiring both **loops and workflows** onto one substrate — so looper's loop is just
> a *machine on the spine*. The port is **wiring + data + a registered machine + a
> walkable skill**, not a new capability with new verbs. And it stays **frugal**:
> looper is a lean reference; the port reuses what already exists.

## Why

[looper](https://github.com/ksimback/looper) **designs agent loops before you run
them**: it coaches a fuzzy idea into a sharp goal, forces *checkable* verification
(programmatic/judge/human), wires a **cross-model review council**, sets
termination guards, and emits a portable loop spec + an in-session handoff + an
external runner. It is a **design layer that sits in front of execution** — the
layer where loops actually fail.

Owner directive (2026-06-20): *"completely port looper into Agency."* Then the
reframe (2026-06-21): *"it's NOT a capability — it's the lifecycle spine, the
looper reimplementation. Lifecycle is the state machine and the event bus of the
system; it wires loops and workflows, so that matches. The reference is more
frugal — it's also a port."*

### Why looper IS the spine (not a sidecar)

Looper is not a domain application like music (Spec 093); it is a **meta-discipline
about agentic loops** — which is exactly what the **Lifecycle pillar** is (Spec
338: the managed state machine; Spec 345: *any* state machine; Spec 349b: the
transition event bus). Every looper concept already has a first-class spine or
substrate primitive — so the port is a *binding*, not a re-implementation:

| Looper concept | Agency spine / substrate primitive (REUSE) | Child |
|---|---|---|
| goal + coaching | **Intent** (`intent.capture`) + clarity gate (322) + goal rubric | 363 |
| typed verification (programmatic/judge/human) | **`gate`** (`gate.check`, typed `GateResult`) | 364 |
| cross-model review council | **`persona`** + **`panel`** + **`delegate`/`jules`** | 365 |
| the loop shape + termination guards | the **`loop` machine** (345) walked via the pillar `ctx.lifecycle.open/move` + a control evaluator | 366 |
| the 7-stage wizard | a **`loop-design` walkable skill** = a `skill:loop-design` machine (346) | 367 |
| `state.json` / `run-log.md` | **provenance** — `manage` reads + the 344/349b event bus | 366 |
| `loop.yaml` / `loop.resolved.json` / `LOOP.md` | a **Document** + **Schema** + `document.render` (179/283/292) | 368 |
| `run-loop.py` + `detect-models` + egress | an emitted template + **DriverRegistry** + one consent gate | 369 |

## The frugal spine layout (no capability folder)

```
agency/_lifecycle_data/machines.json      # + the "loop" machine (DATA, the 345 seam — no engine edit)
agency/_loop.py                           # THE one net-new module:
  open / advance / control_evaluate       #   the walk reducer + termination guards (366)
  compile / emit                          #   graph → loop.resolved.json + document.render (368)
  detect_models / recommend_council       #   model resolution (369) + cross-family council (365)
agency/_lifecycle_data/loop/
  rubrics/    goal · verification · council · control · model-detection   # verbatim from looper
  templates/  loop.yaml · run-loop.py · README · LOOP.md · RUN_IN_SESSION.md
  schemas/    loop.v1 · loop.resolved.v1                                  # Schema nodes (368)
  examples/ai-workflow-mapping/
  skill.py    the loop-design walkable skill (phase graph, 367)
```

**Reuse, no new capability, minimal new verbs.** The agent drives a loop through
the **existing surfaces** — `intent` (goal), `gate` (verify), `persona`/`panel`/
`delegate` (council), the **lifecycle pillar** (`ctx.lifecycle.open(machine="loop")`
/ `.move()`), `document.render` (emit), `manage` (read/provenance), `shell` (argv
boundary), `config`+DriverRegistry (models) — plus the `loop-design` walkable
skill. The only loop-specific code is `agency/_loop.py`; the only substrate touch
is the `loop` entry in `machines.json` (data).

### Ontology — reuse first, minimal net-new

Prefer existing types: goal = **Intent**, council member = **`persona`**,
artefacts = **`Artefact`**, the loop's states = the `loop` machine in
`machines.json` (the `(Lifecycle,state)` enum is the machine-union, Spec 345),
control = props recorded on the `Lifecycle` node. The few irreducible new node
types (`VerificationCriterion`, `EgressPolicy`) register **at the spine** alongside
the machine — NOT via a capability `OntologyExtension` (there is no loop cap).

### The `loop` machine (data in `machines.json` — Spec 345)

```jsonc
"loop": {
  "initial": "planning",
  "states": ["planning","plan_gate","delivering","delivery_gate","completed","failed","canceled"],
  "transitions": {
    "planning":      ["plan_gate","canceled","failed"],
    "plan_gate":     ["planning","delivering","failed","canceled"],
    "delivering":    ["delivery_gate","canceled","failed"],
    "delivery_gate": ["delivering","completed","failed","canceled"],
    "completed": [], "failed": [], "canceled": []
  },
  "terminal": ["completed","failed","canceled"]
}
```

## The reconciliation — native-first, export-second

The owner kept BOTH "native re-expression" AND "portable `loop.yaml` + external
`run-loop.py`". These are two surfaces over one loop that lives on the spine:

```
         the loop lives on the spine
   Intent (goal) · criteria gates · council personas
   Lifecycle{machine:"loop"} + control · EgressPolicy
        │ walk it natively (pillar)        │ project it out (368/369)
        ▼                                  ▼
  ctx.lifecycle.open/move; gates fire,   _loop.compile + document.render →
  council convenes, events on the bus;   loop.yaml · loop.resolved.json ·
  provenance recorded by construction    LOOP.md · RUN_IN_SESSION.md · run-loop.py
```

`loop.resolved.json` is the **shared contract**: the spine walk and the external
runner both honour it. The graph is the source of truth; the resolved JSON is a
faithful projection (`CLAUDE.md` rule 2 applied to a loop).

### The provenance moat (the headline — net-new vs looper)

Looper writes `state.json` + `run-log.md` by hand; nothing connects a verdict to
the criterion it judged to the goal it served. In agency the whole loop is one
`manage.provenance(intent_id)` traversal (Spec 330): every plan/delivery/revision
invocation, every artefact, every gate verdict, every council member. Looper
cannot do this (flat files, no graph). This is the one thing the port exists to
demonstrate at the loop layer.

## Done When (master)

- [ ] **All seven children (363–369) ship Green** with their own Done-When met; each Followup grounded (file:line evidence).
- [ ] **The loop is live on the spine:** `agency search loop` finds the `loop-design` skill; it walks via `develop.skill_walk`; the `loop` machine resolves and passes the per-machine floor — with **no `agency/capabilities/loop/` folder and no new capability**.
- [ ] **The frugal drop-in bar holds:** the port touches ONLY `machines.json` (data) + `agency/_loop.py` + `agency/_lifecycle_data/loop/` (data + the walkable skill) — **ZERO edits to `engine.py` / `registry.py` / `capability.py` / `ontology.py` beyond the spine seam**; everything else is reuse.
- [ ] **Provenance moat lit on a real loop** — `tests/acceptance/test_loop_e2e.py` drives the full pipeline and asserts `manage.provenance(intent_id)` returns the full chain (lands in 369).
- [ ] **Round-trip parity** — a loop walked in-session and run by the emitted `run-loop.py` reach the same gate decisions on looper's ported fixtures (lands in 369).
- [ ] **`TODO.md` updated** (the looper-port row); **MIT attribution to looper** (Kevin Simback) in the `agency/_loop.py` docstring.

## Migration order

```
363 goal ─┐
364 verify├─ foundation (reuse Intent / gate / persona+panel — parallel-safe)
365 council┘
     ▼
366 machine (register the loop machine + the _loop control evaluator)
     ▼
367 wizard (the loop-design walkable skill composing 363–366 + 368)
     ▼
368 emit (_loop.compile + document.render)
     ▼
369 runner (the emitted run-loop.py + egress gate; carries the E2E + round-trip that flip 362 to Shipped)
```

## Appendix A — looper file audit (spine dispositions)

| Looper path | Disposition | Lands in |
|---|---|---|
| `SKILL.md` 7-stage wizard | → the `loop-design` walkable skill (`_lifecycle_data/loop/skill.py`) | 367 |
| `commands/looper.md` | absorbed → the walkable-skill slash mirror (`/agency-loop-design`) | 367 |
| `references/{goal,verification,council,control}-rubric.md` | → `_lifecycle_data/loop/rubrics/` (verbatim) | 363–366 |
| `references/model-detection.md` | → `_lifecycle_data/loop/rubrics/` (verbatim) | 369 |
| `scripts/looper.py` (`compile`/`render`/`session-prompt`) | → `_loop.compile`/`_loop.emit` + `document.render` | 368 |
| `scripts/looper.py` (`detect-models`/`register-model`) | → `_loop.detect_models`/`register_model` over the DriverRegistry | 369 |
| `templates/run-loop.py` | → `_lifecycle_data/loop/templates/run-loop.py`, emitted | 369 |
| `templates/loop.yaml`, `README.md` | → `_lifecycle_data/loop/templates/` + `document.render` | 368 |
| `schemas/loop.v1`, `loop.resolved.v1` | → `_lifecycle_data/loop/schemas/` (Schema nodes) | 368 |
| `examples/ai-workflow-mapping/` | → `_lifecycle_data/loop/examples/` + the E2E fixture | 369 |
| `tests/fixtures/*` (fake host/judge, bad-judge, check-contains) | → acceptance fixtures | 369 |
| `install.sh`/`install.ps1`, `pyproject.toml`, `LICENSE`, `.git*` | **dropped/absorbed** — agency packaging; MIT credit in the `_loop.py` docstring | — |

Every looper path has a disposition (ported → spine / absorbed / dropped) — zero
unaccounted content.

## Followup — Implementation Status (2026-06-21)

**Verdict:** Re-drafted spine-framed (2026-06-21). Reframed from a
`capabilities/loop/` capability to the **lifecycle spine**: the `loop` machine
(data, 345) walked via the pillar, one `agency/_loop.py` module, data under
`agency/_lifecycle_data/loop/`, and a `loop-design` walkable skill — reusing
intent/gate/persona/panel/document/manage/shell/config. Brainstormed spine-first
under the brainstorming discipline (owner forks: spine-not-capability · one
`_loop.py` module · frugal port). All 8 specs (362–369) rewritten spine-framed.
**Implementation starting** — RED→GREEN per child, machine + `_loop.py` first.
