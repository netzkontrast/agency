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

1. **The pillar substrate owns the canonical frame** (`open · move · close` in
   `agency/lifecycle.py`, reached via `ctx.lifecycle` + `lifecycle_*` wire tools;
   `read · find · check · watch` reused from `manage`/`gate`/`jules`) — Lifecycle
   stops being a side-effect of `session_start`/invocation and three hand-rolled
   paths, and becomes one first-class machine an agent opens, moves, and closes
   deliberately. **Not a capability** — a pillar, peer to Intent and Memory.

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

## Architecture — Lifecycle is a PILLAR, not a capability (owner directive, 2026-06-20)

> **Course correction (owner, 2026-06-20): "lifecycle isn't a capability — it's
> its own pillar."** The earlier drafts of this program proposed a `lifecycle`
> *capability* (`agency/capabilities/lifecycle/`). That was wrong, and it created
> the panel's blocker **B1** (a capability verb is subject to the SERVES
> intent-guard, but the engine opens lifecycles internally with no ambient
> intent). Lifecycle is one of the **four pillars** (Intent · Capability ·
> Lifecycle · Memory) — peer to Intent and Memory, **above** the open set of
> capabilities. So it lives where the other concept-pillars live: in the
> **substrate**, not in `capabilities/`.

**The symmetry that fixes it.** Each pillar = a substrate module + a `ctx`
delegator + substrate wire-tools + the capabilities that are its *members*:

| Pillar | Substrate module | `ctx` access | Wire substrate-tool | Member caps (`home=`) |
|---|---|---|---|---|
| **Intent** | `agency/intent.py` (`engine.intent`) | `ctx.intent_id` | `intent_bootstrap` | `discover`, `thinking`, … |
| **Memory** | `agency/memory.py` (`engine.memory`) | `ctx.memory` | `memory_graph_provenance` | `manage`, `reflect`, `document`, … |
| **Capability** | the registry | `ctx.registry` | (search/get_schema/execute) | every craft cap |
| **Lifecycle** | **`agency/lifecycle.py` (`engine.lifecycle`)** ← harden it | **`ctx.lifecycle`** ← NEW | **`lifecycle_open`/`_move`/`_close`** ← NEW | `delegate`, `jules`, `gate`, `subagent`, `branch`, `mode`, `persona`, `select`, `workspace` |

Lifecycle is the **only pillar whose substrate already exists but is unfinished**
— `agency/lifecycle.py` is a real substrate class (`engine.lifecycle`), not a
capability (codegraph-verified). This program **hardens that substrate** and gives
it the two missing arms its peers have: a `ctx` delegator and wire tools.

```
agency/lifecycle.py            # THE PILLAR SUBSTRATE (harden in place; peer to intent.py/memory.py)
  class Lifecycle:             #   the state machine — engine.lifecycle
    open / move / close        #   the write frame (move = SOLE state writer + emits events, 344)
    _transition_table          #   the A2A table (data: agency/_lifecycle_data/transitions.json, 340)
    _parameterizations         #   the variant registry (data: parameterizations.json, 342)
agency/_lifecycle_events.py    # typed LifecycleEvent (344; mirrors _loop_events.py)
agency/_substrate_tools.py     # + LifecycleOpen/Move/Close SubstrateTool (wire; requires_intent like intent_bootstrap)
agency/capability.py           # CapabilityContext gains `ctx.lifecycle` (delegator to engine.lifecycle)
```

> **The SERVES-guard is no longer crossed (B1 resolved).** Substrate (`intent.py`,
> `memory.py`, now `lifecycle.py`) is NOT subject to the per-verb SERVES guard —
> that guard is for `capability_*_*` verbs only. The engine opens a lifecycle via
> `engine.lifecycle.open(...)`; a member capability opens one via
> `ctx.lifecycle.open(...)` (the same machine, intent supplied from `ctx.intent_id`);
> the wire reaches it via the `lifecycle_open` substrate-tool (which takes
> `intent_id` explicitly, exactly as `intent_bootstrap` does). One machine, three
> isomorphic surfaces — the CORE.md "harness-in-harness" ladder.

> **Re-home (Spec 291).** The pillar-package reorg's `agency/<pillar>/<cap>/`
> layout makes this literal: `agency/lifecycle/` becomes the pillar dir holding the
> substrate (`agency/lifecycle/_machine.py`) AND its member caps (`delegate/`,
> `jules/`, `gate/`, …). This program lands the substrate at `agency/lifecycle.py`
> now; 291 moves it into the pillar dir with no behaviour change.

**What this is NOT.** There is **no** `agency/capabilities/lifecycle/` folder, no
`LifecycleCapability(CapabilityBase)`, no `home="lifecycle"` *self*-cap. The
"drop-in capability bar" does not apply — Lifecycle is a pillar, hardened like
Intent (Spec 307 deepened `intent.py`, it did not add an `intent` cap for the
substrate). The member caps already exist and keep their `home="lifecycle"`.

## The canonical frame (CORE.md §3 — substrate methods + ctx + wire tools)

The frame is **substrate `Lifecycle` methods**, surfaced three isomorphic ways
(method · `ctx.lifecycle.*` · `lifecycle_*` substrate-tool) — never a capability
verb:

| Frame member | Surface | What it does | Replaces / reuses |
|---|---|---|---|
| `open(intent_id, kind, agent_id=, parameterization=)` | method · `ctx.lifecycle.open` · `lifecycle_open` tool | Mint a `Lifecycle` SERVING the intent in state `submitted` | the 3 minting paths (`Lifecycle` class · `delegate.fan_out` hand-roll · `develop.SessionLifecycle`) |
| `move(lifecycle_id, to_state, evidence=)` | method · `ctx.lifecycle.move` · `lifecycle_move` tool | The **sole** writer of `state`; enforces the transition table (340); **emits a `LifecycleEvent`** (344) | the unguarded `update({"state":…})` sites (`gate.check` · `lifecycle_gate` · `Lifecycle.move/complete` · `subagent.develop:66` · `delegate`) |
| `close(lifecycle_id, outcome)` | method · `ctx.lifecycle.close` · `lifecycle_close` tool | Terminal `move`; records a Spec 328 **completion `Gate`** keyed to the intent (W-2) | — |
| `advance(lifecycle_id)` | `ctx.lifecycle.advance` (cap-layer reducer) | Run the child's parameterization-declared **observer** (e.g. `jules.verify`) via `ctx.registry` and `move` per its verdict — the ONE observer-dispatch path (Q2/342) | replaces `delegate.join`/`subagent` each hardcoding their observer |
| `read · find` (observe) | `manage.state` / `manage.find` (Memory pillar read-API) | one/many lifecycles + serving intent + agent | **REUSE `manage`** (Spec 290/330) — not re-implemented |
| `check` (observe) | `gate.check` (member cap, Spec 303) → routes its pause through `ctx.lifecycle.move(→input-required)` | a gate predicate that pauses the lifecycle as a *guarded transition* | `gate` member cap, predicate reused |
| `watch` (observe) | `manage.timeline` over the 344 events + `jules.watch` (member) + monitor channel | the recorded transition trail (pull) + the existing pushers | REUSE — see N-2 (it is a pull; push is `jules.watch`) |

> **No new `lifecycle.check`/`lifecycle.watch` verbs (panel F-1).** The observe
> arm is NOT a new surface — `read`/`find` are `manage` (the Memory-pillar read-API
> that already reads lifecycles), `check` stays `gate.check` (now routing its pause
> through the substrate `move`), `watch` is `manage.timeline` over 344's events plus
> the existing `jules.watch`. The pillar OWNS the write machine (`open/move/close`)
> + the parameterization; observation is the Memory pillar's job, reused. This
> kills the dormant-duplicate risk the panel flagged.

> **Discoverability of the substrate frame (panel P1, owner fork Q1 → decided).**
> Substrate-tools don't auto-surface like capability verbs. Decision: **index the
> `lifecycle_open/move/close/advance` tools into `search`** (the same way
> `intent_bootstrap`/`agency_welcome` are surfaced), so the frame is findable
> without a shell capability. No `home="lifecycle"` discovery-cap is added — the
> owner's "it's a pillar" ruling stands; the *index entry*, not a fake cap,
> provides the surface.

### The sole-writer invariant is ENFORCED, not asserted (panel B3)

`move` being the only `state` writer is guarded statically, not just claimed:
an `# AGENCY-DRIFT: lifecycle-state-writer` tag marks the legitimate site
(`Lifecycle.move`), and `scripts/check-drift` (+ an acceptance test) greps
`agency/` for `update(...{"state"` / `record("Lifecycle"` / `record("SessionLifecycle"`
outside `agency/lifecycle.py` and fails on a new occurrence. The invariant is
executable (the Spec 327 `serves_intent_id`-non-null precedent), so it cannot
silently decay.

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
(Spec 342) may *insert* states/edges and *replace* an edge with an
insert-intermediate (the remote-async set replaces `working → completed` with
`working → verify → completed`, so `completed` is reachable only after
verification — CORE.md `COMPLETED ≠ done`).

> **Safety floor (panel F-2 fix — supersedes the earlier "never remove an edge"
> framing).** "Monotone, never remove" was wrong: 342 legitimately replaces
> `working→completed` to force `verify`. The real invariant a parameterization
> must satisfy is **structural, not additive**: (1) every terminal base state
> (`completed · canceled`) stays terminal — no parameterization adds an out-edge
> from it; (2) no base state is **orphaned** — every base state stays reachable
> from `submitted`. Edge *replacement* is allowed under (1)+(2); the
> orphan-check, not edge-monotonicity, is the floor 340 enforces at load.

## Core-feature coverage matrix (what each child ships)

| Child | Slice | Delivers | CORE.md §3 clause |
|---|---|---|---|
| **339** | harden the substrate + write frame | harden `agency/lifecycle.py` (`open · move · close`; `open→submitted`; split gate-shaped `move`); add `ctx.lifecycle` + `lifecycle_*` wire tools; `move` = sole state writer; absorb the 3 minting paths. **Substrate, not a capability** | "verb frame: open · move · close" |
| **340** | state-machine transitions | the enforced A2A transition table (definable registry); the single guard all writes route through; the orphan/terminal floor | "states align with A2A tasks" |
| **344** | transition events | every `move` emits a typed `LifecycleEvent`; **terminal/blocked → durable `Event` node; intermediate churn → monitor channel** (B4 — respects Spec 336) | (substrate for) "read · find · check · watch (observe)" |
| **341** | observe arm (REUSE) | `read · find` ARE `manage`; `check` IS `gate.check`; `watch` IS `manage.timeline` over 344 events + `jules.watch`. **No new observe verbs** (panel F-1) | "read · find · check · watch (observe)" |
| **342** | agent-as-parameterization | the parameterization registry on the substrate (Goal 3 — no per-agent special-casing); member caps declare a parameterization; remote-async inserts `verify`, with `delegate.join` running `jules.verify` so both "done"s are one (B2) | "an agent IS a Lifecycle parameterization … inserts verify; COMPLETED ≠ done" |
| **343** | management discipline | `lifecycle-management` walkable skill (homed on a member cap, e.g. `manage`) + `resume` bridging `SkillRun.resume` | "Gates = input-required → Intent re-entry"; the recursion (a skill IS a Lifecycle) |
| **345** | generic state machine | the **machine registry** (`open(machine=)`, per-machine table, per-machine floor); A2A = default; 342's parameterizations re-express as derived machines; ontology `(Lifecycle,state)` relaxes to the machine-union | "the task/agent state-machine" → ANY state machine (owner) |
| **346** | walkable-skill tracker | every walkable skill derives a `skill:<name>` machine; `SkillRun` = a lifecycle on it; the 3-view tracker (catalogue · live board · history) on `manage`/`skills` | "a skill = an ordered Lifecycle of Phases" (owner) |
| **347** | frugal embedded | the frugal floor (validate·secure·a11y) = non-removable cross-machine invariant; transitions carry the frugal stamp; `frugal` is a drivable machine | Spec 332 frugal, embedded by construction (owner) |

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

## Generalization — Lifecycle as a generic state-machine substrate (owner, 2026-06-20)

> **Owner directive:** *"extend this concept further — so that lifecycle can be
> ANY kind of state machine"* + *"a tracker that tracks walkable skills"* + *"deeply
> embed the frugal skill into lifecycle."* This is the pillar's final widening: A2A
> is not THE machine — it is the **default** machine. The substrate becomes the
> universal state-machine primitive every layer reuses.

**The insight.** Once `move` is the guarded sole writer over a per-target
transition table (339/340), the table need not be A2A-specific. A **machine** is a
named definition — `{name, initial, states, transitions, terminal}` — and A2A is
just `machine="a2a"`. Everything that is "a thing that moves through states" lands
on the SAME substrate as a machine:

| Machine | States (example) | Was |
|---|---|---|
| `a2a` (default) | submitted·working·input-required·…·completed | the fixed `LifecycleState` enum |
| `remote-async` / `reviewed` | a2a + `verify` / `in-review` | parameterizations (342 — now just *machines* derived from a2a) |
| `skill:<name>` | the skill's phases + `paused`·`done` | `SkillRun` walked ad-hoc (343/skill.py) |
| `music:production` / `novel:chapter` | domain stages | hand-rolled domain lifecycles |
| `frugal` | assess→YAGNI→stdlib→native→dep→implement (floor-gated) | the frugal discipline (Spec 332) |

This **subsumes** the parameterization model (342 becomes "a machine derived from
a2a") and unifies N6 fully — one substrate, many machines, no per-domain
hand-rolling. The three new slices below realize it:

- **345 — generic state-machine substrate.** The **machine registry** (definable +
  graph-overridable, `shell.define` pattern); `open(machine=…)` mints the machine's
  `initial`; `move` validates against the lifecycle's machine table (340
  generalized per-machine; the orphan/terminal floor applies per machine). The
  ontology `(Lifecycle, state)` enum relaxes from a single global set to
  **machine-scoped validation** (substrate-layer), with the a2a enum retained as
  the `a2a` machine's states. 342's parameterizations re-express as machines.

- **346 — walkable-skill tracker.** Every walkable skill (`skills.find` catalogue)
  derives a **`skill:<name>` machine** from its phase graph (`skills.index` already
  promotes Skill+Phase nodes). A `SkillRun` becomes a lifecycle on that machine
  (`skill_walk`→`open(machine="skill:<name>")`; phase submit→`move`; hard-gate→
  `move(paused)`; resume→`move(<phase>)`, bridging 343's `SkillRun.resume`). The
  **tracker** is a read surface (on `manage`/`skills`) over three views: the
  **catalogue** (available walkable skills + machine shape), the **live board**
  (in-flight runs, current phase, paused/blocked, resume point), and **history**
  (completed runs) — the single "where is every walk" board.

- **347 — frugal embedded in lifecycle (Spec 332).** Frugal stops being a skill you
  remember to invoke and becomes a **property of how work moves**: (a) the frugal
  **floor** (validate·secure·a11y never cut) is a **non-removable cross-machine
  invariant** — no machine definition may define a path that skips a required
  floor gate (the 340 safety-floor generalized to all machines); (b) every
  transition event (344) carries the `frugal` stamp (the engine already stamps it
  on wire returns — extended to transitions); (c) `frugal` is itself registered as
  a walkable machine (the ladder), so it is both the floor AND a drivable lifecycle.

> **Altitude check (307 lesson, applied again).** This is a *generalization of the
> existing substrate*, not new surface: `open`/`move`/`close` are unchanged in
> shape (they gain a `machine` parameter, defaulting to `a2a` — fully backward
> compatible); the machine registry is data; the tracker REUSES `manage`/`skills`;
> frugal REUSES Spec 332. No new capability, no verb explosion.

## Build slice (the order)

`339` (own the frame; `move` is the only writer; absorb the 3 minting paths) →
`340` (enforce transitions) → `344` (`move` emits transition events) → `341`
(wire the observe suite over those events) → `342` (the parameterization seam;
wire `verify`) → `343` (the discipline + resume) → **`345`** (generalize to any
machine; 342 re-expresses as machines) → **`346`** (walkable-skill tracker on the
`skill:` machine) → **`347`** (frugal embedded as the cross-machine floor). Each is
RED → GREEN → green suite → commit → push, behind acceptance scenarios (CLAUDE.md
rule 7). 344 precedes 341 because the observe suite consumes the events 344 emits;
345 precedes 346/347 because both build on the machine registry.

## Acceptance (the program is "done" when)

1. Opening a Lifecycle (`ctx.lifecycle.open` / `lifecycle_open`), moving it
   `submitted → working → completed`, and reading it back via `manage` is one
   substrate flow — the three minting paths and the ad-hoc `update`s are gone.
2. An illegal transition (`completed → working`) **raises**; every former
   unguarded `state` writer (incl. `subagent.develop:66`) routes through `move`;
   the `# AGENCY-DRIFT: lifecycle-state-writer` guard fails CI on a new writer.
3. A remote-async parameterization inserts `verify`, so a Lifecycle cannot reach
   `completed` without passing through `verify`; `delegate.join`'s "done" equals
   `jules.verify`'s "done" (`COMPLETED ≠ done` enforced, one notion).
4. A failed `check` (`gate.check`) is a `move(→input-required)`; resuming is the
   only permitted exit, looping back to the Intent.
5. Lifecycle is a **pillar** — `agency/lifecycle.py` substrate + `ctx.lifecycle` +
   `lifecycle_*` wire tools — with **no** `agency/capabilities/lifecycle/` folder;
   the `home="lifecycle"` member caps drive the one machine.
6. `scripts/check-drift`, the naming audit, and schema-coverage stay clean; the
   full suite is green; CI is green.

## Panel resolution — blockers folded (2026-06-20)

The `sc:sc-spec-panel` review (`spec-panel-review.md`) raised 5 blockers; all are
resolved in-spec (the 307 precedent — fix in place, retain the review as record):

- **B1 (substrate/capability trust boundary) — RESOLVED by the owner's "it's a
  pillar" directive.** Lifecycle is substrate (`agency/lifecycle.py`), not a
  capability, so it never crosses the SERVES guard. §Architecture rewritten.
- **B2 (the `verify` observer invocation model) — `ctx.lifecycle.advance(lc)`.**
  The parameterization *declares* its observer (`jules.verify` for remote-async,
  `gate.check` for reviewed); a single cap-layer reducer `advance` runs it via
  `ctx.registry` and moves per its verdict (`on_done`/`on_not_done`/`on_error`).
  `delegate.join` + `subagent.develop` both call `advance` — no hardcoded
  member→member dependency. **Updated by the 2nd-pass panel (P2) + owner fork Q2.**
- **B3 (unfalsifiable sole-writer) — static guard.** `# AGENCY-DRIFT:
  lifecycle-state-writer` + a `check-drift` grep (see §Architecture).
- **B4 (344 vs shipped Spec 336) — split by transition class.** Terminal/blocked
  transitions → durable graph `Event` (low-volume provenance); intermediate churn
  → the Spec 021 monitor channel (not the graph). Folded into 344.
- **B5 (no cross-cap e2e) — added.** A `delegate`+`jules`+`lifecycle` round-trip
  acceptance (injected vcs) lands in 342.

Majors folded: W-2 (`close` records a Spec 328 completion `Gate`) · F-2
(monotonicity → orphan/terminal floor, above) · F-3 (unified node schema incl.
`SessionLifecycle` props as the `session` parameterization) · N-2 (`watch` is a
pull — observe is `manage`/`jules`, named honestly) · S-1 (legacy nodes read
`parameterization=""→"default"`; `open→submitted` affects only new lifecycles) ·
auth-required (producer = a future auth-pending parameterization, not the base
flow). Deferred with rationale: C-1 ownership rule + Hi-1 stall detection → 343.

### Second-pass panel folds (post-reframe, owner forks decided 2026-06-20)

The 2nd-pass panel (review §9) raised 2 new blockers on the reframe; both decided
by the owner and folded:

- **P1 (substrate frame discoverability) — Q1: index the `lifecycle_*` tools into
  `search`** (the `intent_bootstrap` precedent); no shell discovery-cap. See
  §"Discoverability" above.
- **P2 (who runs the observer) — Q2: one `ctx.lifecycle.advance` reducer** at the
  capability layer (parameterization declares the observer; `advance` dispatches
  via `ctx.registry`). See B2 (updated) + 342 §"observer dispatch".
- **P3 (`ctx.lifecycle` is a CORE.md change) — accepted:** 339 updates CORE.md
  §CapabilityContext (8→9 fields) + the substrate-tool list. Stated, not silent.
- **P4 (migration risk) — Q3: proof-first.** 339 re-ordered: substrate +
  `ctx.lifecycle` + migrate **`delegate` end-to-end first** as the proof-of-pillar,
  then the other members; `SessionLifecycle`→`session` parameterization is the
  LAST migration slice (Q4), behind a develop/reflect-readers-still-pass gate.

## Followup — Implementation Status (2026-06-20)

Drafted — program master + 6 children (339–344) opened. No code yet; this is the
design record. Two refinement passes on 2026-06-20:

1. **Codegraph deep-analysis** (the "think Ultra / what capabilities need"
   directive): §Why corrected to the verified reality (three divergent lifecycle
   paths; the `jules.verify`/`delegate.join` "done" disconnect; the
   no-transition-events gap), the §"What every capability needs" matrix (N1–N6),
   Goal 3 set as north star, and slice **344 (transition events)** opened.
2. **Architecture correction (owner: "lifecycle isn't a capability — it's its own
   pillar") + spec-panel fold.** Lifecycle reframed from a `lifecycle` capability
   to a **pillar**: substrate `agency/lifecycle.py` + `ctx.lifecycle` + `lifecycle_*`
   wire tools + the existing `home="lifecycle"` member caps (peer to Intent/Memory,
   not a drop-in cap). This dissolved panel blocker **B1**; B2–B5 + majors folded
   in §"Panel resolution". The observe arm is REUSE (`manage`/`gate`/`jules`), not
   new verbs.

The pillar owns the WRITE machine (`open/move/close` + transitions + events +
parameterization); observation is the Memory pillar's job, reused. Children remain
substrate additions, not a new capability folder.

3. **Generalization (owner: "any kind of state machine" + "track walkable skills"
   + "embed frugal").** Three slices opened — **345** (the machine registry: A2A
   becomes the default machine, 342's parameterizations re-express as derived
   machines, `open(machine=)` is backward-compatible), **346** (walkable-skill
   tracker: skills derive `skill:` machines, `SkillRun` is a lifecycle on them,
   a 3-view tracker on `manage`/`skills`), **347** (frugal embedded: the floor is a
   non-removable cross-machine invariant, transitions carry the frugal stamp,
   `frugal` is a drivable machine). All additive on the 345 registry.

**Slice 339a — IMPLEMENTATION STARTED 2026-06-20 (via the agency MCP `tdd`
discipline, intent `9d7af8cf`).** TDD cycle 1 shipped: `agency/lifecycle.py`
hardened — `open→submitted`, `move` is the state-shaped sole guarded writer
(`# AGENCY-DRIFT: lifecycle-state-writer`), `close` replaces the unused gate-shaped
`move`/`complete`. 5 acceptance scenarios (`tests/acceptance/test_lifecycle.py`);
full suite green (exit 0); 194 affected tests pass. Next cycles: `ctx.lifecycle` +
`lifecycle_*` substrate-tools (indexed in `search`) + migrate `delegate`.
