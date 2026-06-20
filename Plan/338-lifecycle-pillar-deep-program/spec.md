---
spec_id: "338"
slug: lifecycle-pillar-deep-program
status: draft
last_updated: 2026-06-20
owner: "@agency"
vision_goals: [2, 4, 9]
depends_on: ["040", "047", "076", "262", "290", "291", "303", "326", "329"]
domain: lifecycle
wave: program-master
---

# Spec 338 — Lifecycle-pillar deep program (master): the managed state machine

> **Program master.** Source of truth for the **Lifecycle-pillar deep
> build-out** UNTIL its children are promoted (Spec 047 precedent: a master
> governs until each child ships, then the child wins). It defines the
> architecture, the canonical verb surface, the transition model, and the
> core-feature coverage matrix the child specs (339–343) all reference. No
> child re-derives the package layout, the verb frame, or the transition
> table — they cite this file.
>
> **This is the Lifecycle analogue of Spec 307 (Intent-pillar deep program)
> and Spec 326 (typed entities).** It applies 307's hard-won refinement
> lesson FROM THE START: deepen the substrate, do not bolt on a side-car;
> the frame is small and CORE-specified; reuse `manage`/`jules`; one
> walkable skill is the discipline. See §"Altitude — what 307 taught us".

## Why (evidence + doctrine + the directive)

**The observed gap.** CORE.md §"Four complete pillars" holds that each of the
four concepts must become a **complete suite of code + tools** — write *and*
read, author *and* observe — reachable through capability verbs, never
hand-written graph queries. The Intent pillar got that depth (Specs 307–325
guided discovery; 326–330 typed entities). The Capability pillar is rich
(`prompt/`, `research/`). The Memory pillar got its read-API (Spec 290 `manage`,
330 typed joins). **Lifecycle is the laggard** — and not on the read side (that
is the *most* covered), but on the **write/own side**: it is the only one of the
four concepts whose canonical verb frame has **no first-class owner**.

CORE.md §3 names that frame precisely:

> **3. Lifecycle** *(state + gates).* The task/agent state-machine. Verb frame:
> **`open · move · close`** (write) + **`read · find · check · watch`** (observe).
> States align with A2A tasks (`submitted · working · input-required · completed
> · failed · canceled`). **An agent (the old "who") is a Lifecycle
> parameterization** — an agent-session is a lifecycle whose transitions/observers
> differ (a remote async agent inserts `verify`; `COMPLETED ≠ done`). Gates =
> `input-required` → Intent re-entry.

**None of that frame exists as a verb surface.** What exists instead:

1. **Lifecycle nodes are minted as side-effects.** `develop.session_start`
   (`develop/_main.py:1128`) mints a `SessionLifecycle`; the invocation pipeline
   (`_invoke.py::InvocationRecorder.open`) records `Invocation` + `Agent` nodes.
   No verb opens a *plain* `Lifecycle` task node with intent.
2. **`Lifecycle.state` is written by UNGUARDED `memory.update`.** Three sites set
   it directly — `gate.check` (`gate/_main.py:55` → `state: "input-required"`),
   the `lifecycle_gate` substrate tool (`_substrate_tools.py:89`), and `reflect`
   (`status: archived` on the session). **There is no transition guard.** The
   A2A enum (`ontology.py:58 LifecycleState`) constrains the *value*, but **any
   state can jump to any state** — `completed → working`, `canceled → submitted`,
   skipping `working` entirely. The state machine is **decorative**.
3. **Observation is scattered.** `manage.whats_next` / `manage.state`
   (`manage/_main.py:372,158`) read Lifecycles serving an intent; `jules` ships a
   watcher (Spec 022); the Spec 076 hook records `Event`s. There is no `read ·
   find · check · watch` frame that unifies them.
4. **The "agent = Lifecycle parameterization" insight is unrealized.** Ten
   capabilities declare `home = "lifecycle"` — `branch · delegate · gate · jules
   · mode · persona · select · subagent · workspace` (+ the implicit session) —
   and each *parameterizes how work proceeds*. But there is **no Lifecycle they
   parameterize**: no managed machine into which a remote-async agent inserts a
   `verify` transition, no place a `persona` or `mode` attaches its variant
   observers. The CORE's single most distinctive Lifecycle idea has no code home.

**The doctrine this serves.** Goal 2 (the provenance moat) says cross-concern
provenance is a single traversal — "every action that SERVES intent Q, the agent
that ran it, **the gate it passed, the state it reached**". That last clause is
only trustworthy if the state machine is *enforced*. A `completed` Lifecycle that
was set by an unguarded `update` skipping `working` is provenance that **lies**.
CORE.md §3 also says `COMPLETED ≠ done` for remote agents — a claim the substrate
cannot currently express because nothing inserts the `verify` step. Completing
the Lifecycle pillar makes the state machine a *fact*, not a label.

## The thesis — one managed machine the parameterizations plug into

A shallow Lifecycle is a *label written ad-hoc*. A deep Lifecycle is a **managed
state machine** with exactly one writer, an enforced transition table, and a
parameterization seam. The pillar becomes complete when:

1. **One capability owns the canonical frame** (`open · move · close` +
   `read · find · check · watch`) — Lifecycle stops being a side-effect of
   `session_start`/invocation and becomes a first-class entity an agent opens,
   moves, and closes deliberately.

2. **`move` is the SOLE writer of `Lifecycle.state`, and it enforces the
   transition table.** Every state change routes through one guard that rejects
   illegal transitions (`completed → working` raises). The A2A states stop being
   decorative; the graph's `state` property becomes trustworthy provenance.

3. **"An agent IS a Lifecycle parameterization" becomes first-class** — the ten
   `home="lifecycle"` caps register *variant* states/transitions/observers into
   the one machine (a remote-async agent's parameterization inserts `verify`
   between `working` and `completed`, encoding `COMPLETED ≠ done`).

4. **Gates are the `input-required` → Intent re-entry loop**, folded into the
   frame: a failed gate is a `move(→input-required)`, and resuming is a
   `move(→working)` that the transition table permits only from `input-required`.

5. **One walkable discipline drives it** — `lifecycle-management` (CORE.md: a
   skill IS a Lifecycle template, so the discipline that manages lifecycles is
   *itself* a Lifecycle — the recursion the canon names), orchestrating the
   already-existing `manage` reads + the new frame verbs.

## Altitude — what 307 taught us (applied here from the start)

Spec 307 §Refinement found its original 16-verb side-car **over-built and at the
wrong altitude**; the fix was to deepen the substrate and let one skill be the
surface. This program **inherits that lesson up front** so it does not repeat the
mistake:

- **The frame is CORE-specified and small.** Seven verbs, not invented —
  `open · move · close · read · find · check · watch` come verbatim from CORE.md
  §3. We do not enumerate a verb per state or per parameterization.
- **The transition table is a definable registry, not code branches** (CLAUDE.md
  #8 — no hardcoded values; CLAUDE.md #75 — definable registries like
  `shell.define`). One data table, overridable, drift-tagged.
- **Observation REUSES `manage` + `jules`, never re-implements.** `read/find`
  compose `manage.state`/`open_intents`; `watch` composes the Spec 076 hook +
  the jules watcher. The dormant-surface audit (CLAUDE.md heuristic #1) applies:
  if `read` duplicates `manage.state`, it is the bug.
- **The typed + read sides are ALREADY SHIPPED — scoped OUT.** `TypedLifecycleState`
  exists (Spec 329); the `manage` read-API over lifecycles exists (Spec 290/330).
  This program does **not** rebuild them — it adds the *write/own* frame and the
  *parameterization* model those reads have been waiting for, and wires the
  existing reads as the observe suite.
- **No parallel tracking system** (CLAUDE.md rule 2). The machine writes the SAME
  `Lifecycle` node the graph already holds; `move` replaces the unguarded
  `update` calls — it does not add a second store.

## Architecture — the `lifecycle` capability (drop-in)

```
agency/capabilities/lifecycle/          # auto-discovered like any cap (Goal 4)
  __init__.py                           # exports LifecycleCapability; re-home anchor for Spec 291
  _main.py                              # LifecycleCapability(CapabilityBase): name="lifecycle", home="lifecycle"
  ontology.py                           # OntologyExtension — reuses core Lifecycle node + adds the
                                        #   transition-table + parameterization registry node types
  clusters/
    _base.py                            #   LifecycleCluster mixin: _recall, _serving, transition-guard helper
    machine.py                          #   open · move · close (the write frame; move = sole state writer)
    observe.py                          #   read · find · check · watch (compose manage + jules; no dup)
    parameterize.py                     #   the agent=parameterization model (Spec 342)
  data/
    transitions.json                    #   the A2A transition table (definable registry, CLAUDE.md #8/#75)
    parameterizations.json              #   variant transition/observer sets (remote-async inserts `verify`)
  templates/
    lifecycle-board.md                  #   the management board Document (Spec 292 convergence)
  references/
    state-machine.md                    #   <!-- doc-source: agency/capabilities/lifecycle/clusters/machine.py -->
    parameterization.md                 #   the agent-as-parameterization contract
```

> **Re-home note (Spec 291).** The pillar-package reorg targets
> `agency/lifecycle/lifecycle/` (the canonical cap of its own pillar). This
> program lands at the current discoverable path (`agency/capabilities/lifecycle/`)
> so it ships before the reorg; the loader transition moves it with the other
> lifecycle-pillar caps (branch · delegate · gate · jules · mode · persona ·
> select · subagent · workspace). No code change at re-home — only the path.

**The drop-in bar (CLAUDE.md).** Adding `lifecycle/` adds verbs + ontology + a
docstring-derived SkillDoc + the `lifecycle-management` walkable discipline — and
**nothing else**. The engine `discover()`s it; the CLI mirrors it (Spec 079); MCP
wires it; emit produces its SKILL.md (Spec 080). If landing it needs an edit
anywhere else, that coupling is the bug to fix — *except* the deliberate,
in-scope replacement of the three unguarded `state` writes (§Why item 2), which
this program OWNS routing through `move`.

## The canonical verb surface (CORE.md §3 — verbatim frame)

| Verb | Role | What it does | Replaces / reuses |
|---|---|---|---|
| `open(intent_id, kind, agent_id=, parameterization=)` | act | Mint a `Lifecycle` SERVING the intent in state `submitted` | the ad-hoc `record("SessionLifecycle"/"Lifecycle")` sites |
| `move(lifecycle_id, to_state, evidence=)` | act | The **sole** writer of `state`; enforces the transition table | the 3 unguarded `update({"state":…})` sites |
| `close(lifecycle_id, outcome)` | act | Terminal `move` to `completed`/`failed`/`canceled` (+ done-gate) | — |
| `read(lifecycle_id)` | act | One lifecycle's full state + serving intent + agent | composes `manage.state` |
| `find(state=, intent_id=, agent_id=)` | act | All lifecycles matching a filter | composes `manage.open_intents` / graph find |
| `check(lifecycle_id, name, passed, evidence=)` | act | A gate predicate → `PASSED` or a `move(→input-required)` | folds `gate.check` semantics |
| `watch(lifecycle_id=, scope=)` | act | Observe transitions/events (poll + Spec 076 hook + jules watcher) | composes existing watchers |

> **`check` and `gate`.** The `gate` capability (`home="lifecycle"`, Spec 303)
> stays — it owns reusable *predicates* and `adjudicate`. `lifecycle.check` is the
> thin frame verb that records a gate **and** performs the `move(→input-required)`
> on failure, so a blocked gate is a *transition*, not an unguarded `update`. The
> gate cap's predicate logic is reused, not reimplemented (the §"observe reuses"
> rule applied to gates).

## The state machine (A2A transition table)

States (closed enum, `ontology.LifecycleState` — unchanged):
`submitted · working · input-required · auth-required · completed · failed ·
canceled`.

The **base** transition table (lands in `data/transitions.json` — definable,
CLAUDE.md #8/#75). `→` = permitted `move`:

```
submitted       → working, canceled
working         → input-required, auth-required, completed, failed, canceled
input-required  → working, canceled            # the gate re-entry loop
auth-required   → working, canceled
completed       → (terminal)
failed          → working, canceled            # retry is an explicit re-open
canceled        → (terminal)
```

Anything not in the table raises (`completed → working`, `submitted → completed`
skipping `working`). The table is **parameterization-aware**: a parameterization
(Spec 342) may *insert* states/edges (the remote-async set inserts `verify` and
rewires `working → verify → completed`, so `completed` is reachable only after
verification — CORE.md `COMPLETED ≠ done`). It may **never** *remove* a base edge
(monotone extension — the safety floor).

## Core-feature coverage matrix (what each child ships)

| Child | Slice | Delivers | CORE.md §3 clause |
|---|---|---|---|
| **339** | scaffold + write frame | the `lifecycle` cap folder + `open · move · close`; `move` becomes sole state writer | "verb frame: open · move · close" |
| **340** | state-machine transitions | the enforced A2A transition table (definable registry); the single guard all writes route through | "states align with A2A tasks" |
| **341** | observe suite | `read · find · check · watch` composing `manage` + `jules` + Spec 076 hook | "read · find · check · watch (observe)" |
| **342** | agent-as-parameterization | the parameterization model; the 10 `home=lifecycle` caps plug variant transitions/observers; remote-async inserts `verify` | "an agent IS a Lifecycle parameterization … inserts verify; COMPLETED ≠ done" |
| **343** | management discipline | `lifecycle-management` walkable skill + `resume`/phases (skill_walk as a Lifecycle projection) | "Gates = input-required → Intent re-entry"; the recursion (a skill IS a Lifecycle) |

## Scoped OUT (already shipped or deliberately deferred)

- **Typed Lifecycle table** — `TypedLifecycleState` shipped (Spec 329). `move`
  writes the graph `Lifecycle`; the typed mirror follows for free (289/329
  one-way projection). No new table.
- **Lifecycle read-API / management dashboard** — `manage.state/whats_next/
  timeline/render` shipped (Spec 290/330). The observe suite (341) *wires* these,
  it does not rebuild them.
- **The FastAPI read surface** (Goal 5/7) — architecturally significant; deferred
  to a human-reviewed spec, not folded here (per the Spec 330 follow-up note).
- **Per-state side-effect hooks beyond `verify`** — YAGNI until a second
  parameterization needs them; the seam (342) is built, extra observers are not.

## Build slice (the order)

`339` (own the frame; `move` is the only writer) → `340` (enforce transitions) →
`341` (wire the observe suite) → `342` (the parameterization seam) → `343` (the
discipline + resume). Each is RED → GREEN → green suite → commit → push, behind
acceptance scenarios (CLAUDE.md rule 7 — Gherkin, no unit tests on internals).

## Acceptance (the program is "done" when)

1. Opening a Lifecycle, moving it through `submitted → working → completed`, and
   reading it back is a pure `lifecycle.*` flow — no hand-written graph query, no
   ad-hoc `update`.
2. An illegal transition (`completed → working`) **raises**; the three former
   unguarded `state` writes now route through `move` and inherit the guard.
3. A remote-async parameterization inserts `verify`, so a Lifecycle cannot reach
   `completed` without passing through `verify` (`COMPLETED ≠ done` is enforced).
4. A failed `check` is a `move(→input-required)`; resuming is the only permitted
   exit, looping back to the Intent (`input-required` → Intent re-entry).
5. The `lifecycle-management` discipline walks the whole pillar over existing
   `manage` reads + the new frame, recording its own SkillRun provenance.
6. `scripts/check-drift`, the naming audit, and schema-coverage stay clean; the
   full suite is green; CI is green.

## Followup — Implementation Status (2026-06-20)

Drafted — program master + 5 children (339–343) opened. No code yet; this is the
design record. Children are pure additions of a cluster module + verbs onto the
339 scaffold, except the in-scope replacement of the three unguarded `state`
writes (339/340), which the program owns. Slice 1 of each child lands the typed
shape; the parameterization data + wet observers follow per the build slice.
