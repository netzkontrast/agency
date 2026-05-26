---
slug: spec-capability-base
type: spec
status: ready
summary: CapabilityContext + an optional CapabilityBase. One typed, per-invocation handle (memory · ontology · schema · template · registry/call · intent · client) replaces ad-hoc string-keyed injection; CapabilityBase lets a capability be written as a class whose verb-methods use self.ctx. Backward-compatible with the functional Capability form; code-mode + reflection discovery unchanged. Proven where noted.
---

# CapabilityBase & CapabilityContext

> **Status: ready.** Gives every capability first-class access to everything it
> needs — without breaking the core concept ([CORE.md](../CORE.md)).

## Why

Today a verb reaches services by string-keyed injection
(`inject: ["memory", "intent_id", "client", "caps"]`). It works but is fragile,
untyped, and exposes only some services — Ontology, Schema, Template, and the
Registry (to call sibling capabilities) are reachable only indirectly. There is
no single handle a capability author asks for.

## CapabilityContext — the one handle

A typed object the engine builds **per invocation** and injects when a verb (or a
`CapabilityBase` method) asks for it. It is a *delegator*, not a new subsystem:

```python
@dataclass
class CapabilityContext:
    memory: Memory            # the one graph
    ontology: Ontology        # the effective, capability-owned ontology
    registry: Registry        # to call sibling capabilities
    intent_id: str            # the Intent everything SERVES
    agent_id: str | None = None
    client: Any = None        # boundary objects (e.g. the Jules backend)

    def call(self, cap, verb, **args):      # delegate to a sibling capability
        ...                                  # == registry.invoke → records an Invocation that SERVES
    def render(self, template, **vars): ...  # render a capability-owned template
    def schema(self, name): ...              # the required-field schema for an artefact kind
    def validate(self, label, props): ...    # ontology.violations(...)
    def record / link / recall / find(...)   # thin Memory pass-throughs
```

- `ctx.call` is `registry.invoke`, so capability→capability composition is
  **provenance by construction** (every nested call records an Invocation that
  `SERVES` the intent) — the same guarantee code-mode gives in-sandbox, now
  available to capability authors directly.
- A **recursion-depth guard** (`ctx.call` carries a depth; raises past a cap)
  covers the one failure mode the panel flagged (cycles) until the engine's
  loop-detection middleware lands.

## CapabilityBase — optional class form

A capability MAY be written as a class extending `CapabilityBase`; the functional
`Capability(name, home, verbs=…, ontology=…)` form stays equally valid (CORE's
Capability set is open — no form is mandatory).

```python
class ReflectCapability(CapabilityBase):
    name = "reflect"
    home = "memory"
    ontology = OntologyExtension(nodes={"Reflection": ["scope", "text"]}, ...)

    @verb(role="act")
    def note(self, scope: str, text: str) -> dict:
        rid = self.ctx.record("Reflection", {"scope": scope, "text": text})
        self.ctx.link(rid, self.ctx.intent_id, "OBSERVED_DURING")
        return {"result": rid}
```

`CapabilityBase.as_capability()` collects `@verb`-decorated methods into the same
`verbs` dict the engine already understands, wrapping each as `cls(ctx).method(...)`
with `inject=["ctx"]` and the method's user-parameter signature preserved for
auto-wiring. `discover()` finds both `Capability` instances and `CapabilityBase`
subclasses.

## What does NOT change (CORE fidelity)

- Capabilities stay the **open, role-tagged craft** (`act`/`transform`/`effect`).
- **Code-mode is still the only public contract** (`search`/`get_schema`/`execute`);
  `ctx` is internal — never a new surface.
- Verbs still auto-wire by reflection from their signatures; the tool surface is
  unchanged. `ctx` is stripped from the MCP schema like any injected param.
- Capabilities still **own their ontology fragments**.
- No dropped idea returns (no four-verb contract, no fixed domains, no `manifest.toml`).

## Deliberately deferred

A mandatory `ToolResult` envelope (`ok/data/warnings/…`) from the prior planning
corpus is **not** adopted: it would bloat code-mode deltas and churn every verb.
It may return later as an opt-in `ctx` helper.

## Migration

Additive. `inject: ["ctx"]` is a new injectable name alongside the existing ones;
old verbs keep working unchanged. Capabilities migrate to the class form (or
`ctx`) opportunistically — `reflect` is the reference migration.
