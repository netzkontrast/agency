---
spec_id: "338"
slug: lifecycle-pillar-deep-program
status: draft
last_updated: 2026-06-20
owner: "@agency"
vision_goals: [2, 3, 4, 9]
depends_on: ["021", "022", "040", "047", "076", "156", "262", "290", "291", "303", "326", "329"]
domain: lifecycle
wave: program-master
---

# Spec 338 — Lifecycle-pillar deep program (master): the managed state machine

> **Program master.** Source of truth for the **Lifecycle-pillar deep
> build-out** UNTIL its children are promoted (Spec 047 precedent: a master
> governs until each child ships, then the child wins). It defines the
> architecture, the canonical verb surface, the transition model, and the
> core-feature coverage matrix the child specs (339–344) all reference. No
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

**What exists today (codegraph-verified, 2026-06-20).** Not "nothing" — worse:
*three divergent, hand-rolled lifecycle paths that share no machine.* A
`codegraph_explore` pass over the live tree found:

1. **A substrate `Lifecycle` class exists but is NOT a capability — and it is
   buggy against the canon.** `agency/lifecycle.py` (64 lines, used by only 2
   files — `engine.py`, `music/drivers_production.py`) carries `open · move ·
   complete · status`. But: (a) `open()` mints state **`working`**, not
   `submitted` — it contradicts CORE.md's `submitted → working` distinction; (b)
   `move(lc_id, gate, ok)` is **gate-shaped, not state-shaped** — it conflates
   "record a gate" with "transition", and only ever reaches `working` or
   `input-required`; (c) `complete()` sets `completed` with **no guard**; (d) it
   writes only 6 of the 7 states (no `auth-required`). It is not discoverable, not
   MCP-wired, not in the CLI — a private helper, not the pillar's owner.
2. **A SECOND minting path hand-rolls the node.** `delegate.fan_out`
   (`delegate/_main.py:488`) does `record_and_serve("Lifecycle", {"state":
   "working", "phase": 0})` directly — bypassing the `Lifecycle` class entirely —
   then `link(lc, agent, "DISPATCHED_TO")` with the literal comment **"an agent IS
   a Lifecycle parameterization"** (line 489). The CORE idea is *commented in the
   code* but realized only as an edge + an `Agent{runtime}` node. Children "start
   `working` (dispatched ≠ done)" — again skipping `submitted`.
3. **A THIRD type, `SessionLifecycle`, is a parallel node.** `develop.session_start`
   (`develop/_main.py:1147`) mints `SessionLifecycle{mode, status}` — a *session*
   is just a Lifecycle parameterization (mode + status), but it is a separate
   label with its own ad-hoc `status` writes (`reflect` archives it).
4. **`state` is written by UNGUARDED `memory.update` from many sites with no
   transition guard.** `gate.check` (`gate/_main.py:55`), the `lifecycle_gate`
   substrate tool (`_substrate_tools.py:89`), `Lifecycle.move/complete`, and
   `delegate` all write `state`/the node directly. The A2A enum (`ontology.py:58`)
   constrains the *value*; **nothing constrains the transition** — `completed →
   working` is accepted. The state machine is **decorative**.
5. **The `verify` discipline exists but is DISCONNECTED from the machine.**
   `jules.verify` (`jules/_main.py:332`, `role="transform"`) already enforces
   `COMPLETED ≠ done` — it independently checks the branch landed on origin via
   `vcs.remote_exists` (`_vcs.py:60`) and emits a `silent_fail_detected` monitor
   event. **But it returns a `{done}` dict and never writes lifecycle state**, and
   `delegate.join` (`delegate/_main.py:521`) computes `done` from the **raw**
   child `state == "completed"` — it does *not* call `jules.verify`. So the
   substrate has two contradictory notions of "done" for the same dispatch, and
   the canon's `verify` step is real but un-wired.
6. **State changes emit NO event.** There is a rich event ecosystem —
   `Event` nodes (`engine.dispatch_hook`, Spec 076, `OBSERVED_DURING` the intent),
   `LoopEvent` (`_loop_events.py`, Spec 156), `MonitorEvent` (`_monitor.py`, Spec
   021) — but a lifecycle **transition records nothing**. An observer
   (`manage`, `jules.watch`, the dogfood loop-detector) can only **poll** `state`;
   it cannot react to a transition, and the transition history is unrecoverable
   except by inferring from `Gate` edges. This is the "lifecycle Events" gap.

**The doctrine this serves — Goal 3, head-on.** GOALS.md Goal 3 is
*"**Agent-uniform lifecycle.** An agent IS a Lifecycle parameterization — Jules,
Claude Code, future LLMs — sharing one hard-gate pattern, one `SERVES` edge, one
recovery flow. **The aim is no special-casing per agent.**"* The findings above
are that special-casing, made concrete: three minting paths, two "done" notions,
a verify step that fires for Jules but not for a local subagent. And Goal 2 (the
provenance moat) says cross-concern provenance is a single traversal — "the gate
it passed, **the state it reached**" — which only holds if the state is *enforced*
and its *transitions are recorded*. A `completed` set by an unguarded `update`
skipping `working`, with no event trail, is provenance that **lies**. Completing
the Lifecycle pillar makes the state machine a *fact* and the agent *uniform*.

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

## What every capability needs from Lifecycle (the deep-analysis matrix)

> The "think Ultra about the Vision goal — what do the capabilities really need
> from Lifecycle" pass (codegraph deep-analysis, 2026-06-20). Each row is a real
> caller found in the tree; the **Needs** column is what it hand-rolls today and
> would instead *call*. The pattern is uniform: every consumer re-implements a
> slice of the state machine because there is no shared one.

| Capability | What it does with lifecycle TODAY (hand-rolled) | What it NEEDS from the pillar |
|---|---|---|
| `delegate` (fan_out/join) | `record_and_serve("Lifecycle", {state:"working"})` per child; `DISPATCHED_TO`/`DELEGATES_TO`/`DRIVES` edges; `join` reduces over raw child `state=="completed"` | `lifecycle.open(parameterization="remote-async"\|"reviewed")`; `join`'s `done` == the **verify** verdict, not raw `completed` (N3) |
| `jules` (verify/watch) | `verify` independently checks `remote_exists` → `{done}` + monitor event; `watch.py` polls sessions | `verify` as the remote-async parameterization's `working→verify→completed` **observer**, writing the `verify` state back (N3); `watch` as a `lifecycle.watch` observer |
| `subagent` (chain_next) | reads child Lifecycle, flips to `done`; `gate.check` for spec-review | the `reviewed` parameterization (insert `in-review`); one `open/move/close` (N1) |
| `gate` (check) | `record("Gate")` + `update(lc,{state:"input-required"})` on fail | `lifecycle.move(→input-required)` so the pause is a guarded transition + an **event** (N4/N5) |
| `develop` (session_start/skill_walk) | mints `SessionLifecycle{mode,status}`; `SkillRun` walks `Phase`s, hard-gate→`input-required`+`resume_from` | a `session` parameterization (mode/status as variant props), not a parallel node (N6); `lifecycle.resume` bridging `SkillRun.resume` (343) |
| `manage` (state/whats_next) | classifies blocked/active/done by reading `state` sets; polls | a real `read/find` to compose (341) + transition **events** so `whats_next` reflects live state without re-scanning (N4) |
| `branch`/`workspace` | VCS ahead/behind/dirty via `_vcs` | a lifecycle whose terminal gate reads the VCS state (the `branch.finish_branch` close) |
| `music`/`novel` (drivers_production) | uses `agency/lifecycle.py Lifecycle` for production stages | a domain parameterization (custom phases) over the SAME machine, not the buggy private class |
| dogfood loop-detector | reads `Event` nodes; transitions invisible | transitions emitted as `Event`s so loops/stalls are detectable (N4) |

**The six cross-cutting needs (N1–N6) the program must satisfy:**

- **N1 — one open/move/close** every consumer calls (replace 3 minting paths + ≥4 state writers). → 339
- **N2 — the `submitted`→`working` distinction** restored (admitted/queued vs. actually running) so `whats_next` is accurate. → 339/340
- **N3 — `verify` wired into the machine** so `delegate.join`'s "done" and `jules.verify`'s "done" are the SAME fact (close the disconnect). → 342
- **N4 — transition events** so observers react instead of poll (the "lifecycle Events" gap). → **344**
- **N5 — transition safety** so a `completed` provenance never lies. → 340
- **N6 — one lifecycle node (parameterized)**, not `Lifecycle` + `SessionLifecycle` + the private class. → 339/342

These needs ARE the slice plan: the program is justified bottom-up by what real
callers re-implement, not top-down from the canon alone.

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
| `move(lifecycle_id, to_state, evidence=)` | act | The **sole** writer of `state`; enforces the transition table; **emits a `LifecycleEvent`** (344) | the 3 unguarded `update({"state":…})` sites |
| `close(lifecycle_id, outcome)` | act | Terminal `move` to `completed`/`failed`/`canceled` (+ done-gate) | — |
| `read(lifecycle_id)` | act | One lifecycle's full state + serving intent + agent | composes `manage.state` |
| `find(state=, intent_id=, agent_id=)` | act | All lifecycles matching a filter | composes `manage.open_intents` / graph find |
| `check(lifecycle_id, name, passed, evidence=)` | act | A gate predicate → `PASSED` or a `move(→input-required)` | folds `gate.check` semantics |
| `watch(lifecycle_id=, scope=)` | act | Observe transitions via the 344 `LifecycleEvent` trail + `jules.watch` + the monitor channel (no poll) | composes existing watchers + 344 events |

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
| **344** | transition events | every `move` emits a typed `LifecycleEvent` (recorded as an `Event` node, `OBSERVED_DURING` the intent) — the "lifecycle Events" gap; consumable by `watch`/`manage`/`monitor`/dogfood (N4) | (substrate for) "read · find · check · watch (observe)" |
| **341** | observe suite | `read · find · check · watch` composing `manage` + `jules.watch` + the monitor channel + the 344 events (no poll) | "read · find · check · watch (observe)" |
| **342** | agent-as-parameterization | the parameterization model (Goal 3 — no per-agent special-casing); the 10 `home=lifecycle` caps plug variant transitions/observers; remote-async inserts `verify`, wiring `jules.verify`+`delegate.join` to one "done" | "an agent IS a Lifecycle parameterization … inserts verify; COMPLETED ≠ done" |
| **343** | management discipline | `lifecycle-management` walkable skill + `resume`/phases (bridges `SkillRun.resume`) | "Gates = input-required → Intent re-entry"; the recursion (a skill IS a Lifecycle) |

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

`339` (own the frame; `move` is the only writer; absorb the 3 minting paths) →
`340` (enforce transitions) → `344` (`move` emits transition events) → `341`
(wire the observe suite over those events) → `342` (the parameterization seam;
wire `verify`) → `343` (the discipline + resume). Each is RED → GREEN → green
suite → commit → push, behind acceptance scenarios (CLAUDE.md rule 7 — Gherkin,
no unit tests on internals). 344 precedes 341 because the observe suite consumes
the events 344 emits.

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

Drafted — program master + 6 children (339–344) opened. No code yet; this is the
design record. **Refined 2026-06-20 after a codegraph deep-analysis pass** (the
"think Ultra about the Vision goal / what capabilities need" directive): the §Why
was corrected to the verified reality (three divergent lifecycle paths —
`agency/lifecycle.py` + `delegate.fan_out` hand-roll + `develop.SessionLifecycle`;
the `jules.verify`/`delegate.join` "done" disconnect; the no-transition-events
gap), the §"What every capability needs" matrix (N1–N6) was added grounding the
program bottom-up, the north star was set to **Goal 3 (agent-uniform lifecycle —
no special-casing per agent)**, and a new slice **344 (transition events)** was
opened for the "lifecycle Events" gap. Children are pure additions of a cluster
module + verbs onto the 339 scaffold, except the in-scope absorption of the three
minting paths + the unguarded `state` writes (339/340), which the program owns.
