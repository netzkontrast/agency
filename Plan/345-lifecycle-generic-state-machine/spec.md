---
spec_id: "345"
slug: lifecycle-generic-state-machine
status: draft
last_updated: 2026-06-20
owner: "@agency"
vision_goals: [3, 4]
depends_on: ["075", "338", "339", "340", "342"]
domain: lifecycle
wave: program-master
parent_spec: "338"
---

# Spec 345 — Lifecycle as a generic state-machine substrate (any machine)

> Child of the Lifecycle-pillar deep program (Spec 338). Owner directive: *"extend
> this concept further — so that lifecycle can be ANY kind of state machine."* A2A
> stops being THE machine and becomes the **default** machine; the substrate
> becomes the universal state-machine primitive every layer reuses. This
> **subsumes** the parameterization model (342 → "a machine derived from a2a").

## Why

After 339/340, `move` is the guarded sole writer over a per-target transition
table. The table is currently A2A-specific (`agency/_lifecycle_data/transitions.json`).
But nothing about the machinery is A2A-specific — a transition table is a transition
table. Today every "thing that moves through states" that ISN'T A2A is hand-rolled
on its own node type: `SkillRun` phases (`agency/skill.py`), music production
stages (`music/clusters/lifecycle.py`), novel chapters (`novel/clusters`), jules
session states (`JulesSession.state`, a separate enum). That is the N6 fragmentation
the pillar exists to end — and 342's parameterizations are a *partial* generalization
(A2A + extra states) that already proves the seam. 345 finishes it: **one substrate,
many machines.**

## Design

### A machine is a named definition (`agency/_lifecycle_data/machines.json`)

```jsonc
{
  "a2a": {                              // the DEFAULT machine (the current A2A table)
    "initial": "submitted",
    "states": ["submitted","working","input-required","auth-required","completed","failed","canceled"],
    "transitions": { "submitted": ["working","canceled"], "working": ["input-required","auth-required","completed","failed","canceled"], "...": [] },
    "terminal": ["completed","canceled"]
  },
  "remote-async": { "derives": "a2a", "add_states": ["verify"],
                    "replace": {"working": {"remove": ["completed"], "add": ["verify"]}, "verify": ["completed","input-required","failed"]},
                    "observer": {"capability":"jules","verb":"verify","on_done":"completed","on_not_done":"input-required","on_error":"verify"} },
  "skill:<name>": { "...": "derived from the skill's phase graph by Spec 346" }
}
```

- Definable + graph-overridable (the `shell.define` pattern, Spec 075): seed in
  data, override via a `Machine` node; drift-tagged `# AGENCY-DRIFT: lifecycle-machines`.
- `derives` makes **342's parameterizations a special case** — a parameterization
  IS a machine that derives from `a2a` and adds/replaces edges. The
  `parameterizations.json` (342) merges into `machines.json`; `effective_table`
  becomes `resolve_machine(name)` (apply `derives` + `add_states`/`replace`).
- The orphan/terminal **floor** (340) is enforced **per machine** at load: every
  machine's terminal states stay terminal, no state orphaned from `initial`.

### Substrate changes (`agency/lifecycle.py`)

```python
def open(self, intent_id, agent=None, *, machine="a2a") -> str:
    m = resolve_machine(machine)
    lc = self.m.record("Lifecycle", {"state": m["initial"], "phase": 0, "machine": machine})
    ...                                  # default machine="a2a" → byte-identical to 339 behaviour

def move(self, lc_id, to_state, *, evidence="") -> str:
    node = self.m.recall(lc_id) or {}
    m = resolve_machine(node.get("machine", "a2a"))
    if to_state not in m["states"]:      # per-MACHINE validation (was the global enum)
        raise ValueError(f"{to_state!r} not in machine {node.get('machine')!r}")
    if to_state not in m["transitions"].get(node.get("state"), []):
        raise IllegalTransition(...)     # 340 guard, per-machine table
    ...
```

`machine` defaults to `a2a`, so all existing callers (and 339's behaviour) are
unchanged — this slice is **purely additive**.

### The ontology change (the one real widening)

Today `FIELD_ENUMS[("Lifecycle","state")] = LIFECYCLE_STATES` — a single global
closed enum. With many machines, a lifecycle's `state` is `"draft"` or `"mastered"`
for a domain machine, which the global enum would reject. Resolution (frugal, least
disruptive):

- The ontology `(Lifecycle, state)` enum **relaxes to the UNION of all registered
  machines' states** (computed from the registry, not hand-listed — single source).
  The a2a enum (`LifecycleState`) is retained as the `a2a` machine's state set.
- The **precise** per-machine check moves to substrate `move` (above) — the
  ontology guards "is a known state somewhere", the substrate guards "is a legal
  state+transition for THIS machine." Two layers, no global freeze.

### What this slice does NOT do

- No change to `open/move/close` *shape* beyond the `machine=` param (default a2a).
- No skill/domain machines yet — 346 derives `skill:` machines; domain caps
  (music/novel) re-home onto machines in their own follow-ups.
- No new capability — the registry is substrate data; `machine` is a node prop.

## Acceptance (Gherkin)

```gherkin
Scenario: the default machine is a2a and behaviour is unchanged
  When I open a lifecycle with no machine specified
  Then its machine is "a2a" and its state is "submitted"

Scenario: a custom machine drives its own states
  Given a registered machine "pipeline" with states [queued, running, shipped] initial "queued"
  When I open a lifecycle with machine "pipeline"
  Then its state is "queued"
  And move(running) succeeds but move(shipped) from queued raises IllegalTransition

Scenario: a parameterization is just a derived machine
  Given machine "remote-async" derives "a2a" and replaces working->completed with working->verify->completed
  When I open with machine "remote-async" and move working
  Then move(completed) from working raises (must pass verify)

Scenario: the per-machine floor rejects an orphaned state at load
  Given a machine whose transitions orphan its terminal state
  Then resolve_machine raises at load (the floor holds per machine)

Scenario: the ontology accepts any registered machine's state
  Given machine "pipeline" with state "shipped"
  Then recording a Lifecycle{state:"shipped", machine:"pipeline"} passes ontology validation
```

## Followup — Implementation Status (2026-06-20)

Not started — opened by the owner's "any kind of state machine" directive. Generalizes
340's per-target table into a **machine registry**; `open(machine=)` + per-machine
`move` validation; 342's parameterizations re-express as derived machines; the
ontology `(Lifecycle,state)` enum relaxes to the union of registered machines'
states with precise per-machine checks at the substrate. Backward compatible
(`machine="a2a"` default). Foundation for 346 (skill machines) + 347 (frugal floor
per machine).
