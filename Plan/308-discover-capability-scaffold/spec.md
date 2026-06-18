---
spec_id: "308"
slug: discover-capability-scaffold
status: draft
last_updated: 2026-06-18
owner: "@agency"
vision_goals: [4, 9]
depends_on: ["016", "024", "080", "081", "291", "307"]
domain: intent
wave: program-master
parent_spec: "307"
---

# Spec 308 — `discover` capability scaffold + intent-pillar code structure

> Child of the intent-pillar deep program (Spec 307). This is the **foundation
> slice**: it lands the `discover` package skeleton, its consolidated ontology,
> the docstring-derived SkillDoc, and the derived `discover-usage` walkable —
> the empty-but-discoverable capability the other 17 children fill in.

## Why

Spec 307 §"Architecture" calls for a `prompt`-shaped capability so the Intent
pillar gains a peer to the Capability pillar's richest member. Before any
discovery *behaviour* can land, the **drop-in shell** must exist: a folder the
engine `discover()`s, an `OntologyExtension` registering the program's node
types/edges/enums/schemas, and a docstring that *derives* its Agent Skill
(CLAUDE.md derivability audit — `Use when:`/`Triggers:`/`Red flags:`). This slice
is deliberately thin on behaviour and complete on **structure** — it is the
"add a folder, gain a complete capability" bar (CLAUDE.md "drop-in bar") made
concrete for the intent pillar.

Landing the scaffold first means: (1) every later child is a *pure addition* of a
cluster module + verbs, never a structural change; (2) `check-drift` and the
naming-audit see `discover` from day one; (3) the ontology is registered once,
so children populate node *instances* without re-touching the schema.

## Design

### Package layout (mirrors `agency/capabilities/prompt/`)

```
agency/capabilities/discover/
  __init__.py            # exports DiscoverCapability; re-home anchor for Spec 291
  _main.py               # DiscoverCapability(CapabilityBase): name="discover", home="capability"
  ontology.py            # discover_ontology = OntologyExtension(...)  — Spec 307 ontology table
  clusters/
    __init__.py
    _base.py             # DiscoverCluster mixin: _recall_intent, _record_turn, _session helpers
  data/
    ambiguity-signals.json   # seed heuristics (CLAUDE.md #8 — definable, not frozen)
    interview-beats.json     # the adaptive beat library
  templates/
    discovery-session.md     # Spec 292 convergence Document
    intent-brief.md
  references/
    elicitation.md           # <!-- doc-source: agency/capabilities/discover/clusters/interview.py -->
    askuser-contract.md
```

`_main.py` carries the **capability docstring** that derives the SkillDoc
(Spec 080) — `Use when:` a fresh or vague intent needs guided discovery before
work begins; `Triggers:` an underspecified ask, a missing acceptance test, a
"not sure what I want yet"; `Red flags:` starting work against an unconfirmed or
ungrounded intent → run `discover.interview` first.

### The cluster-mixin pattern (`_base.py`)

Following `prompt/clusters/_base.py`: `DiscoverCluster` is a mixin
`DiscoverCapability` composes, exposing shared helpers so each child's cluster
module stays thin:

- `_recall_intent(intent_id="")` → the serving intent's node (defaults to
  `ctx.intent_id`, the Spec 091 ambient pattern).
- `_record_turn(session_id, beat, kind, question, answer)` → records an
  `ElicitationTurn` + `ELICITS` edge (used by interview/clarify/scope).
- `_session(seed)` / `_session_of(intent_id)` → open or recall a
  `DiscoverySession` and its `DISCOVERED` edge.
- `_clarity_inputs(intent_id)` → the signal bag Spec 322's score reads.

### Ontology registration (the Spec 307 table, verbatim)

`ontology.py` registers all 7 node types, 7 edges, 4 enums, and 6 schemas from
Spec 307 in one `OntologyExtension`, plus the `guided-discovery` skill slot
(populated by Spec 323). `Citation` is **not** re-declared — `GROUNDS` reuses
the `research` capability's existing `Citation` node (Spec 044), per the
no-duplicate rule.

### What this slice does NOT do

No verb behaviour beyond a single `discover.status()` smoke verb that returns the
registered ontology surface (proves the cap is wired). Every other verb in the
Spec 307 table is a child. This keeps the scaffold a true foundation.

## Tests (RED → GREEN; invariants, not snapshots — rule 8)

- **Discovery (Goal 4):** `discover` appears in the live registry after boot with
  zero edits outside its folder — assert it is in `engine.registry` and its
  SkillDoc validates (`develop.validate_skill`), computed from the live registry.
- **Ontology completeness:** the registered node/edge/enum/schema **set** equals
  the Spec 307 table — assert set-equality against the table parsed from this
  spec's fixture, not a pinned count, so adding a node updates one place.
- **Drop-in bar:** `scripts/check-drift` exits 0 with `discover` present (install
  dry-run + capability-test-gap + tag inventory all clean).
- **No `Citation` redefinition:** `discover`'s ontology does NOT declare a
  `Citation` node — assert `"Citation" not in discover_ontology.nodes` (reuse,
  not duplicate).
- **CLI mirror (Spec 079):** `agency discover status` runs and returns the same
  surface as the MCP `capability_discover_status` (isomorphism).

## Acceptance

Adding the `discover/` folder yields a complete, discoverable, walkable,
CLI-exposed, MCP-wired capability whose ontology registers the whole program's
node surface — and **nothing outside the folder changed**. Each of 309–325 is
now a pure addition of one cluster module + its verbs.

## Followup — Implementation Status (2026-06-18)

- **Status: draft.** Scaffold slice of the Spec 307 program. Land FIRST so every
  sibling is an addition. The `status` smoke verb is the only behaviour; it is
  removed or absorbed once `discover.interview` (309) lands as the real entry.
- **Open question (resolve at build):** land at `agency/capabilities/discover/`
  (current loader) vs. `agency/intent/discover/` (Spec 291 target). Default:
  current path + re-home with the 291 transition, to ship before the reorg.
