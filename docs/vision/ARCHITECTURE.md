---
slug: vision-architecture
type: vision
status: ready
summary: The runtime — one engine (FastMCP) hosts three domains over the four-verb contract; one substrate (GraphQLite context graph) is the only persistent state; workflows are graph paths; artifact drivers move bytes to user storage; CodeMode renders the three domain surfaces.
---

# Architecture — one engine, one graph, three domain surfaces

## One engine

**FastMCP** is the only runtime. It hosts all three domains in one process. Its
public surface is the **four-verb contract**:

- `mcp__list_tools` · `mcp__call_tool` · `mcp__list_skills` · `mcp__dispatch_skill`

Every domain tool (`mcp__agentic_*`, `mcp__workflow_*`, `mcp__context_*`) is an
entry in the one registry served over that contract.

## One substrate

The **context graph** is the only persistent state: a single SQLite file at
`context/_store/ontology.db`, accessed through the GraphQLite extension (Cypher
+ node/edge primitives + graph algorithms). Typed nodes (`Skill`, `Tool`,
`Phase`, `Gate`, `Artefact`, `Row`, `Continuation`, …) and typed edges
(`PRECEDES`, `BLOCKS`, `PRODUCES`, `DERIVED_FROM`, `DISPATCHED_TO`, …) record
everything the system knows.

## Discovery

At boot the harness scans the three fixed domains. Under each it discovers rows
(`<domain>/<row>/manifest.toml`) and derives their skill/tool names
domain-first. Cold boot lists only the four verbs and stays under the
documented token budget; CodeMode lazily renders the three domain surfaces on
demand.

## Workflows are graph paths

A workflow is a path through the graph: traverse edges from the current state
to a goal, invoke the tool/skill at each node, emit provenance edges. When a
step is missing the engine either **blocks-and-prompts** (default) or
**lazy-links** the missing nodes (opt-in per row). A yield (blocked, or
awaiting the user) is a `Continuation` node — there is no state file on disk.

## Drivers — the user-facing edge

Artifact drivers map `Artefact` nodes to external storage (`fs` is mandatory;
`repo` / `s3` / `http` / `drive` follow). The graph holds the record; the
driver moves the bytes. System metadata never leaks into user storage.

## CodeMode

A skill or tool may declare a CodeMode preference. The harness then renders
that domain's call surface as a code sandbox in which the domain's functions —
including a row's, e.g. `agentic.jules.*` — are callable, with an
envelope-archiving interceptor applied inside the sandbox.
