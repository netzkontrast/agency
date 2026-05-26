---
slug: specs-index
type: spec-index
status: ready
summary: The contracts for each part of the v4 four-concept model. One spec per part — the Engine substrate, the four concepts (intent, capability, lifecycle, memory), and the skills-and-gates step-graph model. Read CORE.md, OVERVIEW.md, ARCHITECTURE.md first.
---

# Specs — the contracts (per part)

Each spec is the authoritative contract for one part of the system. Read
[`../CORE.md`](../CORE.md) (the model), `../OVERVIEW.md` (the narrative), and
`../ARCHITECTURE.md` (the runtime) first. Every spec carries a **Status** line;
parts proven by the engine are marked **proven**.

| Spec | Owns |
|---|---|
| [engine](engine.md) | the substrate — code-mode IS the contract (`search`/`get_schema`/`execute`); capabilities self-register; engine-guard middleware |
| [intent](intent.md) | the human-owned root; `capture · confirm · amend`; the `SERVES` spine |
| [capability](capability.md) | the open craft; verbs role-tagged `act` / `transform` / `effect`; `<capability>.help`; the Invocation record |
| [capability-base](capability-base.md) | `CapabilityContext` (the one typed handle) + optional `CapabilityBase`; first-class memory/ontology/schema/template/registry/intent access |
| [lifecycle](lifecycle.md) | the task/agent state-machine; `open · move · close` + `read · find · check · watch`; A2A states; agent-as-parameterization; gates |
| [memory](memory.md) | the moat — bi-temporal append-only graph; `record · link · supersede` + `recall · find · validate`; `project`; one-traversal provenance |
| [skills-and-gates](skills-and-gates.md) | skills as atomic, gated, progressively-disclosed Lifecycle step-graphs; gates / intent-verification / askuser as `elicit` steps |

The isomorphic verb frame across the concepts:

| Concept | write verbs | observe / read verbs |
|---|---|---|
| **intent** | `capture · confirm · amend` | (read via memory) |
| **capability** | open craft verbs, role-tagged `act` / `transform` / `effect` | `<capability>.help` |
| **lifecycle** | `open · move · close` | `read · find · check · watch` |
| **memory** | `record · link · supersede` | `recall · find · validate` (+ `project`) |
