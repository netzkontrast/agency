---
spec_id: "347"
slug: frugal-embedded-lifecycle
status: draft
last_updated: 2026-06-20
owner: "@agency"
vision_goals: [3]
depends_on: ["332", "338", "340", "344", "345"]
domain: lifecycle
wave: program-master
parent_spec: "338"
---

# Spec 347 — Frugal embedded in lifecycle (the cross-machine floor)

> Child of the Lifecycle-pillar deep program (Spec 338). Owner directive: *"deeply
> embed the frugal skill into lifecycle."* Frugal (Spec 332) stops being a
> discipline an agent must remember to invoke and becomes a **property of how work
> moves through any state machine** — the non-removable floor every machine
> inherits, the stamp every transition carries, and a drivable machine in its own
> right.

## Why

Spec 332 ships the **frugal** discipline: the ladder `YAGNI → stdlib → native →
dep → 1-line` and the **floor** *validate · secure · a11y never cut*. Today it is
surfaced as a hook nudge + a wire-return stamp (`frugal_prefix()`), i.e. *advisory*
— an agent can ignore it. The owner wants it **embedded**: work that moves through
a lifecycle should be frugal *by construction*, not by reminder. The generic
state-machine substrate (345) makes this possible — frugal becomes a substrate-level
invariant across every machine, exactly as the safety floor (340) is.

## Design — three depths of embedding

### 1. The frugal FLOOR is a non-removable cross-machine invariant

345 enforces a per-machine structural floor (terminal-preservation, no orphans).
347 adds the **frugal floor** to that check: a machine definition may not define a
"done"-reaching path that **skips a required floor gate** (validate · secure ·
a11y). Concretely, a machine that produces a shippable artefact (reaches a terminal
`completed`) must route through the gate states/observers that assert the floor, or
`resolve_machine` rejects it at load — the same shape as 345's orphan-check. This
makes "validate/secure/a11y never cut" a property the registry *guarantees*, not a
docstring. (The ladder — YAGNI→…→1-line — stays advisory guidance; only the
**floor** is hard, matching Spec 332's own "floor never cut" framing.)

### 2. Every transition carries the frugal stamp

The engine already prepends `frugal_prefix()` to wire returns (`_frugal`, Spec 332
M2). 347 extends that to **lifecycle transition events** (344): each `LifecycleEvent`
(and its monitor-channel sibling) carries the active frugal level, so the provenance
trail records the discipline in force when each transition fired — frugal becomes
auditable per move, not just per wire return. (Capture is full — CLAUDE.md #76.)

### 3. `frugal` is itself a registered machine (the ladder, drivable)

Register a `frugal` machine in the 345 registry:

```
machine "frugal":
  initial: "assess"
  states:  ["assess","yagni","stdlib","native","dep","implement","floor-check","done"]
  transitions: assess->[yagni], yagni->[stdlib,implement], stdlib->[native,implement],
               native->[dep,implement], dep->[implement], implement->[floor-check],
               floor-check->[done,implement]     # floor-check can bounce back
  terminal: ["done"]
```

So the frugal discipline is BOTH the cross-machine floor (depth 1) AND a lifecycle
you can `open(machine="frugal")` and walk — the ladder as a real state machine, not
just a hook string. A `develop`/`tdd` walk's implementation phase can open a nested
`frugal` lifecycle to make the ladder explicit and recorded.

### What this slice does NOT do

- No change to the frugal *content* (Spec 332 owns the ladder/floor definition —
  single source; 347 reuses `frugal_signals`/`frugal_prefix`, never re-defines).
- No hard-gating the *ladder* (YAGNI→…→1-line stays advisory; only the floor is
  enforced — matching Spec 332).
- No new capability — the floor check lives in `resolve_machine` (345), the stamp
  in the event emitter (344), the `frugal` machine in the registry data.

## Acceptance (Gherkin)

```gherkin
Scenario: a machine that skips the floor is rejected at load
  Given a machine whose path to "completed" skips its required validate gate
  When resolve_machine loads it
  Then it is rejected (the frugal floor is non-removable)

Scenario: a floor-honouring machine loads
  Given a machine that routes to completed through its validate/secure/a11y gate
  Then resolve_machine accepts it

Scenario: transition events carry the frugal stamp
  Given a lifecycle that moves working->completed
  When I read its transition event
  Then it records the active frugal level

Scenario: frugal is a drivable machine
  When I open a lifecycle with machine "frugal"
  Then its state is "assess"
  And it can be walked assess->yagni->...->implement->floor-check->done

Scenario: the floor definition has a single source (Spec 332)
  Then 347 reads the floor from Spec 332's frugal module, not a copy
```

## Followup — Implementation Status (2026-06-20)

Not started — opened by the owner's "deeply embed frugal into lifecycle" directive.
Three depths: (1) the frugal floor (validate·secure·a11y) becomes a non-removable
cross-machine invariant in `resolve_machine` (345); (2) transition events (344)
carry the frugal stamp; (3) `frugal` is registered as a drivable machine (the
ladder). Reuses Spec 332 (single source for the floor/ladder); only the floor is
hard, the ladder stays advisory. Builds on 345 (machine registry) + 344 (events).
