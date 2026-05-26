---
slug: spec-engine
type: spec
status: ready
summary: The Engine — the substrate, NOT a concept. One FastMCP server + one bi-temporal graph. Code-mode IS the contract — the public surface is exactly search/get_schema/execute; capability tools are discovered via search and called from inside execute. Capabilities self-register by reflection and auto-wire one tool per verb. Engine guards (quality-score, loop-detection, compaction, Slot/quota) are middleware. Proven in the v0.1 plugin.
---

# Engine

> **Status: proven in the v0.1 plugin.** The Engine is the host process; it is
> NOT a concept. It hosts the four concepts (Intent, Capability, Lifecycle,
> Memory).

## Concept

ONE FastMCP server + ONE bi-temporal graph host everything. **Code-mode IS the
contract** — the public surface is exactly `search` / `get_schema` / `execute`
(no separate four-verb surface). Capabilities and concepts are data the Engine
serves; the Engine itself adds no concept vocabulary. Cross-cutting guards are
middleware.

## Interface — code-mode is the contract

```
search(query)        -> deltas: discover the tools that match
get_schema(tools)    -> the input schemas for the tools you'll call
execute(code)        -> run Python that chains tools in-sandbox; return only deltas
```

That is the **entire surface**. Inside `execute`, `await call_tool(name, params)`
is in scope; the agent discovers a tool with `search`, gets its schema with
`get_schema`, and calls it from inside `execute`. No flat tool list ever loads
into context. The same contract is exposed isomorphically over **MCP · Skills · a
bash CLI** (`agency/cli.py` + `AGENTS.md`).

**Proven:** with code-mode on, `list_tools` returns exactly
`{search, get_schema, execute}`; the bash CLI drives the identical contract over
a persisted graph and yields identical results.

## Capabilities self-register and auto-wire (reflection)

The Engine does not hand-wire a tool per verb. It `discover()`s every
`Capability` in `agency/capabilities/` (`pkgutil` + `importlib`) and AUTO-WIRES
one MCP tool per verb from the verb function's signature (`inspect.signature`).
Adding a capability is **adding a file**. Params a verb declares in its `inject`
list (e.g. `client`, `caps`, `memory`, `intent_id`) are supplied by the Registry,
not the caller, and are hidden from the tool's schema.

## Token efficiency

The agent writes code that chains tools and filters/joins **in-sandbox**;
intermediate results stay in the sandbox; only filtered **deltas** reach context
(Anthropic "Code execution with MCP", 2025-11-04 — up to −98% tokens). Because
every `call_tool` records an Invocation, the executable chain mirrors itself into
the provenance graph.

**Proven:** an `execute` block lints several candidate skills (`transform`),
picks the cleanest, and dispatches a Jules agent (`effect`) on it — many calls
in-sandbox, one small delta returned, and the chain appears as a connected
provenance subgraph.

## Tool naming

`capability_<capability>_<verb>` — underscores, ≤64 chars, no dots; the client
injects the `mcp__` prefix.

## Engine guards (cross-cutting middleware — NOT concepts)

| Guard | Role |
|---|---|
| quality-score | confidence/quality signal on a step's output; can halt below threshold |
| loop-detection | halts repeating, non-progressing cycles |
| compaction checkpoint | named checkpoint that prunes working context; full record stays in Memory |
| `Slot` / quota accounting | tracks concurrent dispatch slots + external quotas; Lifecycle reads it to gate fan-out |

## Interactions

- Auto-wires verbs derived from each `Capability`'s `(name, verb)` by reflection.
- Cold boot exposes only `search` / `get_schema` / `execute`; tool-masking (not
  tool-removal) keeps the surface — and its KV-cache prefix — stable.
- Builds the EFFECTIVE ontology (core + each capability's `OntologyExtension`) and
  injects it into Memory, which enforces it on `record` / `link` / `update`.
