# The capability system

<!-- doc-source: agency/capability.py -->
<!-- doc-hash: 350831fee6a8e5c1 -->

`agency/capability.py` defines how a capability is authored, compiled, registered, and
invoked. It is the single most load-bearing module.

## Authoring a capability — `CapabilityBase` + `@verb`

```python
class MyCapability(CapabilityBase):
    name = "mycap"
    home = "capability"                 # or "lifecycle" / "memory"
    ontology = OntologyExtension(...)   # optional: nodes/edges/enums/skills/schemas

    @verb(role="transform")             # role ∈ {transform, act, effect, gate-ish}
    def do_thing(self, x: str) -> dict:
        """First line = the verb's brief (kept short — token economy).

        Inputs: … Returns: … chain_next: …
        """
        return {"result": ...}
```

- **`role`** classifies the verb: `transform` (pure compute), `act` (produces a
  document/artefact), `effect` (external side-effect — the provenance moat depends on
  this tag). The role is recorded on every `Invocation`.
- **`inject=[…]`** asks the registry to pass a boundary by name (`vcs`, `embedder`,
  `runner`, `skills_client`). `ctx` is always injected.
- A verb reaches engine services through **`self.ctx`** (a `CapabilityContext`).

`as_capability()` compiles the class to a frozen `Capability`: it collects `@verb`
methods, deep-copies the ontology, and — per **Spec 080** — *derives* the `SkillDoc`
from the module docstring (`Use when:` / `Triggers:` / `Red flags:`) when none is set,
and — per **Spec 081** — injects a derived `<cap>-usage` walkable skill when the
capability authored none.

## `CapabilityContext` — the one handle a verb gets

A delegator over engine services (never a new public surface):

- `ctx.memory` — the graph; `ctx.intent_id` — the serving intent (ambient).
- `ctx.record(label, props)` / `ctx.link(a, b, REL)` — write nodes/edges.
- `ctx.call(cap, verb, **args)` / `ctx.spawn(...)` — invoke a sibling verb (records an
  Invocation; depth-guarded against cycles).
- `ctx.get_driver(name)` — resolve an external `Driver` (Spec 002); raises
  `DriverMissing`.
- `ctx.registry`, `ctx.ontology`, `ctx.engine` — escape hatches for introspection.

## `Registry` — discovery, injection, the invoke moat

- `register(cap)` / `get(name)` / `names()` — the live capability set.
- `injectors` — the boundary providers (derived from the engine's `DriverRegistry`).
- **`invoke(memory, intent_id, cap, verb, **args)`** — the moat:
  1. **rejects** any `intent_id` that is not a labelled `Intent` node (no orphan
     side-effects);
  2. records an `Invocation` that `SERVES` the intent **before** calling (a failing run
     is still auditable);
  3. injects the `CapabilityContext`;
  4. runs the verb; on a `ToolResult`, records warnings / typed error / `archived_to`
     and converts `artefacts_written` + a `data["artefact"]` into `Artefact` nodes with
     `PRODUCES` edges, then unwraps to `.data` for the lean wire shape.

  Spec 286-A3 decomposed this monolith into an orchestrator over four collaborators —
  `IntentGuard` (step 1), `ParameterInjector` (step 3), `InvocationRecorder` (step 2),
  `ResultProcessor` (step 4) — with the logic in `agency/_invoke.py`. Behaviour is
  byte-identical; the steps above still describe what happens, only the *where* moved.
  Verbs are also typed `Verb` value objects now (Spec 286-A4), not raw dicts, with a
  Mapping bridge so `spec["fn"]`-style access still works.

## The Driver family (Spec 002)

Also defined here: `Boundary` / `Driver` marker Protocols, `DriverRegistry`
(`register`/`register_factory`/`get`/`has`/`names`/`backend`/`readiness`), and
`DriverMissing`. See [drivers.md](drivers.md).

## The drop-in bar, enforced here

Because `as_capability()` derives the SkillDoc + usage-walk and `Registry` auto-wires
everything, a capability folder needs **only** verbs + ontology + a docstring. Adding a
verb named `intent_id` collides with the reserved injected param — that and the
`as_capability` decorator-placement caveat are the two known authoring gotchas.
