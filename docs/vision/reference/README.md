# Architecture

How agency is built, module by module. Each page documents one part of the engine,
carries a **doc-drift marker** (the source files it describes), and points at the code.

> **Read [overview.md](overview.md) first** — the four concepts, the wire contract, and
> the bootstrap flow that ties every module below together.

## The module map

| Page | Documents | What it is |
|---|---|---|
| [overview.md](overview.md) | — | The four concepts · the 3-tool wire contract · bootstrap flow |
| [engine.md](engine.md) | `agency/engine.py` | Bootstrap, capability discovery, the substrate tools, boundaries |
| [capability-system.md](capability-system.md) | `agency/capability.py` | `CapabilityBase`, `@verb`, `Registry`, `CapabilityContext`, `DriverRegistry` |
| [ontology.md](ontology.md) | `agency/ontology.py` | Nodes · edges · enums · `OntologyExtension`, strict merge |
| [memory.md](memory.md) | `agency/memory.py` | The bi-temporal graph store, provenance traversal |
| [intent-lifecycle-gate.md](intent-lifecycle-gate.md) | `agency/intent.py`, `agency/lifecycle.py` | Three of the four concepts: the human root, the state machine, gates |
| [toolresult.md](toolresult.md) | `agency/toolresult.py` | The `ToolResult` / `TypedError` return envelope |
| [skills.md](skills.md) | `agency/skill.py`, `skill_emit.py`, `disclosure.py` | Skill schemas, the walker, derived/authored skills, emission |
| [drivers.md](drivers.md) | `agency/capability.py` (Driver family) | The `Boundary`/`Driver` contract + `DriverRegistry` (Spec 002) |
| [token-economy.md](token-economy.md) | `agency/_tokens.py` | The `TokenCounter` boundary + the token-economy doctrine |
| [install-cli.md](install-cli.md) | `agency/install.py`, `agency/cli.py` | The three surfaces: MCP code-mode · bash CLI · the plugin install |
| [helpers.md](helpers.md) | `agency/_*.py`, `cache.py`, `templates.py` | The supporting modules (monitor, runner, predicates, cache, …) |

## The one-paragraph architecture

A **FastMCP engine** (`engine.py`) discovers **capabilities** (`capability.py`) from
`agency/capabilities/`, each of which extends a single bi-temporal **graph**
(`ontology.py` + `memory.py`) and exposes **verbs**. The engine presents exactly three
tools to the wire — **`search` · `get_schema` · `execute`** — so an agent writes code
against the live verb surface (code-mode) and only the return crosses back. Every verb
records an `Invocation` that `SERVES` an `Intent`, so the whole system is one auditable
provenance graph. External I/O (git, Jules, audio, the token counter, the Skills API)
is isolated behind **Drivers** (`drivers.md`) resolved by name from a `DriverRegistry`.

<!-- doc-source: agency/engine.py -->
<!-- doc-hash: 5bea6367a1045f0b -->
