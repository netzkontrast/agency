---
slug: spec-engine
type: spec
status: ready
summary: The Engine — the substrate, NOT a concept. One FastMCP server + one bi-temporal graph. Public surface = the four-verb contract (list_tools/call_tool/list_skills/dispatch_skill) + one execute(code) code-mode tool. Engine guards (quality-score, loop-detection, compaction, Slot/quota) are middleware. Seed-proven: real FastMCP four-verb surface + code-mode.
---

# Engine

> **Status: specced; seed-proven where noted.** The Engine is the host process;
> it is NOT a concept. It hosts the four concepts (Intent, Capability, Lifecycle,
> Memory).

## Concept

ONE FastMCP server + ONE bi-temporal graph host everything. The Engine exposes a
tiny stable surface (the four-verb contract) plus one code-mode tool, and
enforces cross-cutting guards as middleware. Concepts and capabilities are data
the Engine serves; the Engine itself adds no concept vocabulary.

## Interface — the four-verb contract + code-mode

```
list_tools(...)     -> deltas: available verbs (schemas deferred)
call_tool(name, args) -> result
list_skills(...)    -> deltas: available skills
dispatch_skill(name, args) -> result
execute(code)       -> code-mode: chain tools in-sandbox, return only deltas
```

`list_tools` / `call_tool` are MCP-native; `list_skills` / `dispatch_skill` are
surfaced as tools (MCP has no skill RPC). These are the **entire cold-boot
surface**; every concept verb is reached through `call_tool`, its schema deferred
until requested (progressive disclosure).

**Seed-proven:** the seed builds a real FastMCP server whose tools include
`agency_list_skills`, `agency_dispatch_skill`, `memory_graph_provenance`, and the
capability verbs — all matching the MCP-conformant name pattern
`^[A-Za-z0-9_]{1,64}$`.

## Code-mode (the token-efficiency primitive — seed-proven)

On demand the Engine hides the raw tools behind **`search` / `get_schema` /
`execute`**. The agent writes code that chains tools and **filters/joins
in-sandbox**; intermediate results stay in the sandbox; large payloads return as
`elided_ref` handles; only filtered **deltas** reach context (Anthropic "Code
execution with MCP", 2025-11-04 — up to −98% tokens). Because every `call_tool`
records an Invocation, the executable chain mirrors itself into the provenance
graph.

**Seed-proven:** with code-mode on, `list_tools` returns exactly
`{search, get_schema, execute}`; an `execute` block chains a `transform`
(`capability_syllables_count`) into an agent capability
(`capability_jules_patch`), runs 4 calls in-sandbox, and returns one small delta
— and the chain appears as a connected provenance subgraph.

## Tool naming

`<concept>_<capability>_<verb>` — underscores, ≤64 chars, no dots; the client
injects the `mcp__` prefix. (The skill/code-mode serialized forms are a
serializer detail, not a top-level concern.)

## Engine guards (cross-cutting middleware — NOT concepts)

| Guard | Role |
|---|---|
| quality-score | confidence/quality signal on a step's output; can halt below threshold |
| loop-detection | halts repeating, non-progressing cycles |
| compaction checkpoint | named checkpoint that prunes working context; full record stays in Memory |
| `Slot` / quota accounting | tracks concurrent dispatch slots + external quotas; Lifecycle reads it to gate fan-out / `reclaim_slot` |

## Interactions

- Renders verbs derived from `(concept, capability, verb)`.
- Cold boot exposes only the four-verb contract (+ code-mode); tool-masking (not
  tool-removal) keeps the surface — and its KV-cache prefix — stable.
- References the pinned Intent by id so prompt prefixes stay append-only.
