# Overview — the four concepts, the wire contract, the bootstrap flow

<!-- doc-source: docs/vision/CORE.md agency/engine.py agency/capability.py -->
<!-- doc-hash: 15a6549d6ce8ccf0 -->

The authoritative model is [../CORE.md](../CORE.md). This page is the
engineering-level summary: what the pieces are and how a call flows through them.

## The four concepts (one substrate)

Agency models everything an agent does as nodes in **one provenance graph**. There are
exactly four concepts — multiplying them is the bloat the canon forbids:

| Concept | Node | Owns | Module |
|---|---|---|---|
| **Intent** | `Intent` | the human-owned *why/what* — the root every action serves | `intent.py` |
| **Capability** | — | the *how* — verbs grouped by domain, self-registered | `capability.py` |
| **Lifecycle** | `Lifecycle`, `Gate` | task/agent state + the gates that pause it | `lifecycle.py`, `gate` cap |
| **Memory** | every node/edge | the bi-temporal graph itself + recall/provenance | `memory.py` |

A `reflect.note` is Memory; an `intent.premortem` reasons about Intent; `develop`'s
disciplines are Lifecycle templates (skills); a capability verb is Capability. No fifth
concept, no new public tool, no new role-tag is added without deleting the equivalent
weight elsewhere.

## The wire contract — three tools

No matter how many capabilities or verbs exist, the engine exposes exactly **three
substrate tools** plus a few bootstrap tools:

- **`search(keyword)`** → discover capabilities + verbs (tiered, token-budgeted).
- **`get_schema(name)`** → the precise signature of one verb.
- **`execute(code)`** → run code against the live verb surface **inside the sandbox**;
  only the return value crosses back (**code-mode** — CORE.md:9-18).

Bootstrap tools (the documented exceptions): `intent_bootstrap`, `agency_welcome`,
`agency_doctor`, `lifecycle_gate`, `memory_graph_provenance`. This fixed set is guarded
by `tests/test_naming_audit.py`.

**Code-mode is the contract.** An agent does not call verbs one-RPC-at-a-time; it writes
a short program that chains verbs in the sandbox (`call_tool("capability_x_y", {...})`),
and only the conclusion returns. This is why adding verbs never widens the wire.

## How a call flows (bootstrap → invoke → provenance)

1. **Bootstrap** (`Engine.__init__`, `engine.py`): build the core `Ontology`; discover
   every `CapabilityBase` under `agency/capabilities/` (+ any `extra_capabilities`);
   merge each capability's `OntologyExtension` **strictly** onto core; register its
   verbs; build the `DriverRegistry` (the six boundaries); validate each capability's
   docstring-derived `SkillDoc`. Nothing is written to the graph at bootstrap.
2. **Intent first**: every verb requires an `Intent`. An agent mints one via
   `intent_bootstrap` (or `agency intent …` on the CLI). `Registry.invoke` rejects any
   call whose `intent_id` is not a labelled `Intent` node.
3. **Invoke** (`Registry.invoke`, `capability.py`): records an `Invocation` that
   `SERVES` the intent **before** calling (so even a failure is auditable), injects the
   `CapabilityContext` (memory, ontology, registry, drivers, the serving intent), runs
   the verb, and unwraps a `ToolResult` into the lean wire shape — recording warnings,
   typed errors, and `PRODUCES` artefact edges as side-effects on the Invocation.
4. **Provenance**: because every action is an `Invocation SERVES Intent` (+ `PRODUCES`,
   `OBSERVED_DURING`, `PASSED`/`BLOCKED_ON`, …), a full audit of any goal is **one graph
   traversal** (`memory_graph_provenance(intent_id)`). This is the moat.

## The drop-in-capability bar

The whole architecture is in service of one test: **add a folder under
`agency/capabilities/<name>/`** — verbs + an `OntologyExtension` + a docstring that
*derives* its Agent Skill — **and nothing else**, and agency gains a complete,
discoverable, walkable, CLI-exposed, MCP-wired, publishable capability. If adding a
capability needs an edit anywhere else, that coupling is the bug. See
[../../guide/extending.md](../../guide/extending.md).
