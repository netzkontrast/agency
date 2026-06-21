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

- [x] `workflow` self-registers (357); the **`develop-spec`** Lifecycle skill on
      `workflow.ontology.skills` walks the 14 phases one at a time via
      `develop.skill_walk`, each phase recorded as a `Phase` node SERVING the
      intent (provenance asserted: ≥8 Phase nodes after the design walk).
- [x] Phases carry `verbs` cues binding existing verbs (no re-implementation,
      panel B1); the improve-loop (9) is a HARD design gate that pauses at
      `input-required`, and the **ADR-approval (11)** is the second hard gate (the
      hinge — a spec can't pass it to `inprogress` until decisions are approved).
- [x] Schema-coverage + check-drift green (a skill, not a verb — no new wire
      surface); full suite run before done.

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
| `discover` triage (phase 2) under-delivers on a vague seed | `discover.interview` **shipped** (Spec 309 — adaptive beat-chain) + `discover.clarify`/`clarity_gate` (311/322); phase 2 binds them directly. Forward-compatible with the remaining `discover` children |
| ADR hinge gate (11) deadlocks a spec | Owner override (provenance-stamped) per 355; `board`/`index` show exactly what's blocking |

## Interconnects

- **354/355/356** — the ADR craft + gate + extraction the hinge phases drive.
- **357** — the spec-state verbs this capability hosts and drives.
- **359** — Brooks-lint phase in the improve-loop.
- **307/309 (discover)** — the triage phase.
- **018 (skill walker)** — `develop-spec` is a Lifecycle template walked one phase
  at a time.
- **047 (clusters)** — the plan/spec/review/build through-line.

## Spec-panel findings folded in (panel 2026-06-20)

- **B1 (Fowler — is `workflow` a new capability, or a `develop` discipline?).**
  The `develop-spec` skill mostly *re-binds* `develop`'s own disciplines
  (brainstorm/plan/spec-panel/tdd/review/execute already live there). The
  conceptually-cheaper shape is: **`develop-spec` is a new `develop` discipline**
  (a peer Lifecycle template), and the **only genuinely-new surface** — the
  spec-state verbs `move_spec`/`index`/`board` (357) — lands on `develop` or
  `manage`, not a standalone cap. **Recommended shape: discipline-in-`develop` +
  spec-state verbs on `develop`.** The owner framed this as "the workflow
  capability thing", so this spec preserves the standalone-`workflow`-capability
  option as an **owner decision at implementation** — but the panel's
  recommendation (and Spec 359's own Brooks-lint, applied reflexively) favours not
  minting a capability that exists only to call other capabilities' verbs.
  *Net: the 14-phase skill + the spec-state verbs ship regardless; only their
  HOME is the open decision.*
- **B2.3 (Crispin — the improve-gate exit criterion).** Phase 9 ("improve") is no
  longer a vibe: the design gate passes iff **(a)** spec-panel findings are folded,
  **(b)** `intent.brooks_lint` returns **no `block` finding** (359), and **(c)**
  the owner confirms. Decidable + human-gated; the loop re-enters phases 7–8 until
  (a)+(b) hold, then waits on (c).
- **M2 — discover triage:** `discover.interview` shipped (Spec 309); phase 2 binds
  it directly (failure-mode row corrected above).

## Followup — Implementation Status (2026-06-21)

### B1 home-decision — RESOLVED
The owner directed "the workflow capability thing" and 357 already shipped the
standalone **`workflow` capability** (hosting the spec-state verbs). So the
`develop-spec` discipline lands on `workflow.ontology.skills` — no relitigation.

### Done — Slice 1 (TDD, shipped 2026-06-21)
- The **`develop-spec`** walkable Lifecycle skill (14 phases) on
  `workflow.ontology.skills`, modelled as a discipline (each phase carries
  `verbs` cues binding the SHIPPED verbs — `intent.capture` · `discover.interview`
  · `develop.brainstorm` · `research.fetch`/`codegraph_explore` ·
  `discover.acceptance` · `develop.write_spec` · `develop.spec_panel` ·
  `intent.brooks_lint` · `workflow.move_spec`+`adr.extract_decisions` ·
  `adr.approve` · `workflow.move_spec`+`adr.hints` · `develop.tdd` ·
  `develop.verify`+`workflow.move_spec`). No re-implementation (panel B1).
- Three HARD gates: **improve** (9, the design gate), **adr-approve** (11, the
  ADR hinge), **done** (14). `develop.skill_walk` delivers one phase at a time
  and pauses at each; resume confirms the gate and continues.
- 3 acceptance scenarios (`workflow_skill.feature`): registered+walkable · pauses
  at the improve gate (+≥8 Phase provenance nodes) · resume → pauses at the
  adr-approve hinge. workflow_skill + spec_state 9 green; schema 44; drift clean.

### Still — Slice 2 (step verbs + e2e dogfood)
- The step sugar verbs (`start`/`design`/`open_spec`*/`approve_decisions`/
  `begin_impl`/`finish`) — individually callable, chainable, same provenance.
  (*357 already has `workflow.open_spec` minting the SpecLifecycle; the 358
  phase-10 step needs a different name, e.g. `to_open`, to avoid the collision.)
- The end-to-end dogfood (353 Slice-2 acceptance): a real intent walked through
  develop-spec → /draft → folded findings → /open + decision drafts → approved
  ADR → guarded /inprogress + hints → /done, one provenance tree.
- Optional: promote phases to executable `invoke` bindings (auto-run the bound
  verb) where the phase IS a single deterministic verb call.
