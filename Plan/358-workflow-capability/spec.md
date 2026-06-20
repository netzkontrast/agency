---
spec_id: "358"
slug: workflow-capability
status: draft
last_updated: 2026-06-20
owner: "@agency"
depends_on: ["353", "354", "355", "356", "357", "359", "307", "018", "047"]
vision_goals: [1, 2, 6]
domain: core
wave: adr-workflow
affects:
  - agency/capabilities/workflow/__init__.py
  - agency/capabilities/workflow/_main.py
  - tests/acceptance/features/workflow.feature
  - tests/acceptance/test_workflow.py
---

# Spec 358 — `workflow` capability: the repo-development lifecycle

> Capstone of **353**. The `workflow` capability hosts the spec-state verbs (357)
> and the walkable **`develop-spec`** Lifecycle skill that chains intent →
> triage → brainstorm → research → acceptance → spec → spec-panel → Brooks-lint →
> improve-loop → ADR draft+approval → implementation (hints loaded) → done. One
> MCP tool per step, individually callable and chainable.

## Why

Owner directive: *"Ziel ist … einen Lifecycle für die Arbeit am Repo zu
erstellen … beginnend mit Intent-Erfassung und Interview-Triage — Brainstorm und
ggf. Research (auch im Repo, über CodeGraph) — dann Akzeptanzkriterien — dann eine
Spec — diese Spec-Panel und jetzt neu auch tiefer Brooks-lint hinterfragen — dann
improve, im Loop bis das Design gut ist — und dann anfangen mit Entwicklung. Für
jeden Workflow-Step eigene MCP-Tools (die aber auch gechaint werden können)."*

agency already owns every *step* — `discover` (interview), `develop`
(brainstorm/plan/tdd), `develop.spec_panel`, `research`, `adr` (354–356),
`workflow` spec-state (357), `intent.brooks_lint` (359). What it lacks is the
**through-line**: a single Lifecycle template that orders them, delivers one phase
at a time (Spec 018 walker, token-bounded), guards the ADR hinge, and records the
whole repo-development episode as provenance under one intent. This capability IS
that through-line — it makes the owner's process the *default* way to build the
repo, dogfooding Goal 6 end to end.

## Design

### A new capability `agency/capabilities/workflow/`

Hosts (a) the **spec-state verbs** specified in 357 (`move_spec`, `index`,
`board`) and (b) the **`develop-spec` Lifecycle skill** (an `ontology.skills`
template, Spec 018). Drop-in bar: a folder + `_main.py` + ontology + docstring;
the only outside edits are the documented substrate-set update + `# AGENCY-DRIFT`
tag (rule 6).

### The `develop-spec` skill (a walkable Lifecycle template)

Each phase `invoke`-binds an existing capability verb (Spec 018 `invoke` binding),
so the walker chains real tools and records each phase as provenance — no
re-implementation:

| # | Phase | Binds → | Produces | Gate |
|---|---|---|---|---|
| 1 | `intent` | `intent.capture` | intent_id, acceptance | — |
| 2 | `triage` | `discover` (interview — Spec 307/309) | clarified scope, questions resolved | — |
| 3 | `brainstorm` | `develop.brainstorm` | design candidates, tradeoffs | — |
| 4 | `research` | `research.*` + **CodeGraph** (`codegraph_explore` over what already exists) | prior-art, affected symbols | — |
| 5 | `acceptance` | (author) | Gherkin-shaped acceptance criteria | — |
| 6 | `spec` | `develop.write_spec` → `Plan/draft/NNN` | spec.md authored | — |
| 7 | `spec-panel` | `develop.spec_panel` | panel findings folded | — |
| 8 | `brooks-lint` | `intent.brooks_lint` (359) | conceptual-integrity findings folded | — |
| 9 | `improve` | (loop 7–8) | design_good | **hard** — design gate; loops until passed |
| 10 | `open` | `workflow.move_spec(→open)` then `adr.extract_decisions` (356) | spec in `/open`, decision drafts | — |
| 11 | `adr-approve` | `adr.approve` (355) per drafted decision | decisions approved | **hard** — the ADR hinge |
| 12 | `inprogress` | `workflow.move_spec(→inprogress)` (guarded by `spec_decisions_ready`) + `adr.hints` loaded | spec in `/inprogress`, hints in context | — |
| 13 | `build` | `develop.tdd` / `develop.plan_execute` | implementation, tests green | — |
| 14 | `done` | `workflow.move_spec(→done)` after `develop.verify` | spec in `/done`, verified | **hard** — done gate (COMPLETED ≠ done) |

The walker delivers ONE phase at a time (`develop.skill_walk("develop-spec", …)`),
so context stays bounded (Goal 1); every phase is a `Phase` node `SERVES` the
intent (Goal 2). Phases 10–12 are the ADR hinge the owner specified: a spec
**cannot** reach phase 12 until phase 11's gate passes (`spec_decisions_ready`,
356/355).

### Per-step MCP tools, chainable

Every phase's bound verb is already an independent MCP tool (auto-wired). For
ergonomics `workflow` also exposes thin **step verbs** that are individually
callable and return `chain_next` so an agent can either walk the whole skill or
fire one step:

| Verb | Role | Wraps |
|---|---|---|
| `start(purpose, deliverable, acceptance)` | act | phase 1–2 (intent + triage), returns the walk handle |
| `design(intent_id)` | act | phases 3–9 (brainstorm→research→spec→panel→brooks-lint→improve) |
| `open_spec(spec_id)` | effect | phase 10 (move→open + extract_decisions) |
| `approve_decisions(spec_id)` | effect | phase 11 (adr.approve loop) |
| `begin_impl(spec_id)` | effect | phase 12 (guarded move→inprogress + load hints) |
| `finish(spec_id)` | effect | phase 14 (verify + move→done) |

These are sugar over the walker + the underlying caps — they record the same
provenance (the moat is never bypassed). The canonical contract stays
`search · get_schema · execute` (Goal 5); these are reached through `execute`.

### Cluster coherence (rule 5)

`develop-spec` spans the **plan · spec · review · build** clusters of Spec 047 —
it is their coherent through-line, not a new parallel pattern. The spec-panel,
review, and tdd disciplines are *reused* (bound), not duplicated. This spec
extends the cluster master's pattern; it does not break it.

## Done When

### Slice 1 — capability + skill walk

- [ ] `workflow` self-registers; `develop.skill_walk("develop-spec", …)` walks the
      14 phases one at a time, each phase recorded as provenance under the intent.
- [ ] Phases 1–9 bind their existing verbs and produce their outputs; the
      improve-loop (9) is a hard design gate that re-enters 7–8 until passed.
- [ ] Substrate-set tests green with `workflow` added; full suite run before done.

### Slice 2 — the ADR hinge + step verbs

- [ ] Phases 10–12 enforce the hinge: `open_spec` extracts decisions (356);
      `begin_impl` is **blocked** until `approve_decisions` clears the 355 gate
      (`spec_decisions_ready`), then loads `adr.hints` into the build context.
- [ ] The step verbs (`start … finish`) are individually callable and chainable,
      recording the same provenance as the full walk.
- [ ] **End-to-end dogfood** (the 353 Slice-2 acceptance): a fresh intent walked
      through `develop-spec` yields a `/draft` spec, folded panel+Brooks findings,
      a `/open` move with extracted decision drafts, an approved ADR, a guarded
      `/inprogress` move with hints loaded, and a `/done` close — all one
      provenance tree.

## Failure modes (Nygard)

| Failure | Response |
|---|---|
| `workflow` re-implements brainstorm/panel/tdd instead of binding them | Phases `invoke`-bind existing verbs (Spec 018); a test asserts no duplicated discipline logic |
| The 14-phase walk dumps everything into context at once | Walker discloses one phase at a time (Goal 1); asserted by the per-phase return contract |
| Step sugar verbs bypass the provenance moat | Sugar verbs route through the same caps/walker; provenance recorded identically (tested) |
| `discover` (phase 2) is still a scaffold (Spec 307/308) | Phase 2 degrades gracefully to a documented interview prompt until `discover` ships its verbs (Spec 309); the binding is forward-compatible |
| ADR hinge gate (11) deadlocks a spec | Owner override (provenance-stamped) per 355; `board`/`index` show exactly what's blocking |

## Interconnects

- **354/355/356** — the ADR craft + gate + extraction the hinge phases drive.
- **357** — the spec-state verbs this capability hosts and drives.
- **359** — Brooks-lint phase in the improve-loop.
- **307/309 (discover)** — the triage phase.
- **018 (skill walker)** — `develop-spec` is a Lifecycle template walked one phase
  at a time.
- **047 (clusters)** — the plan/spec/review/build through-line.

## Followup — Implementation Status (2026-06-20)

### Done
- Spec authored (design depth).

### Still
- Slice 1 (capability + walk) then Slice 2 (ADR hinge + step verbs + e2e dogfood)
  via TDD. Land after 354–357 + 359.
