# Capability roadmap

The capability surface the engine grows into, organized as clusters. Each cluster
is a candidate capability (or a facet of an existing concept); the table records
its role(s), the concept(s) it touches, a one-line spec sketch, and its
disposition (built in v0.1, or specced-next). New capabilities arrive by dropping
a file in `agency/capabilities/` — each self-registers and owns its ontology
fragment.

| Cluster | Role(s) | Concept(s) | Spec sketch | Disposition |
|---|---|---|---|---|
| `plugin` (skill + plugin authoring) | act, transform | Capability · Lifecycle · Engine | scaffold a manifest, author skills/commands, marketplace entries, lint skills (CSO rules) | **built (v0.1)** |
| `develop` (dev disciplines) | process | Lifecycle | brainstorm · plan · tdd · debug · verify · spec-panel · review, as walkable gated skills | **built (v0.1)** |
| `reflect` (durable memory) | act, transform | Memory | scope-tagged insight nodes + recency/keyword recall | **built (v0.1)** |
| `jules` (remote async agent) | effect, transform | Capability · Lifecycle | dispatch a remote coding session; `COMPLETED ≠ done` `verify` | **built (v0.1)** |
| `music` (domain bundle) | act | Capability · Memory | the album conceptualizer (a 7-phase gated skill) + `Album` types | **example extension** (`examples/music.py`, loaded via `extra_capabilities`) |
| `delegate` | effect, transform | Capability · Lifecycle · Memory | fan a task out across children under a quota + join; `DELEGATES_TO`/`REDUCES_INTO` edges; built on `ctx.spawn` with `jules` as first driver | **built** |
| `gate` | transform, process | Lifecycle · Memory | a stateless precondition/quality predicate that passes or blocks a Lifecycle phase, recording evidence | facet of Lifecycle |
| `craft` | act | Capability · Intent · Memory | produce a domain artefact from an Intent + upstream artefacts | the open `act` set |
| `transmute` | transform | Engine · Capability | pure functions over artefacts: views, indexes, summaries, tool-list shaping | the open `transform` set |
| `commit-effect` | effect | Lifecycle · Memory | mutate external state (fs, git, cloud), verify the world reached the intended terminal state | the open `effect` set |
| `research` | agent, transform | Capability · Memory | a lead agent fans out to specialists; a verifier gate admits only cited claims | composition (delegate + craft + gate) |
| `navigate` | transform | Lifecycle · Memory · Intent | read-projections: "where am I, what's blocked, what's next" against acceptance | `project` / `provenance` |
| `wire-handlers` | Engine | Engine · Memory | the substrate: reflection-based discovery + auto-wiring, the extensible ontology | the engine itself |

## The verdict (why so few primitives)

Most clusters are **facets of the four concepts**, not new top-level primitives —
`gate`/`craft`/`transmute`/`commit-effect` are just the role-tags (`act` /
`transform` / `effect`) of the open Capability set; `navigate` is a read
projection; `wire-handlers` is the engine. Multiplying concepts would re-introduce
bloat. After the collapse, the one net-new primitive — **`delegate`** (agent
fan-out + quota + join, with `jules` as its first driver) — is now **built**.
**`research`** remains: a *composition* (delegate → craft → gate), to ship as a
skill template rather than a primitive.

## Confidence

~0.9 that the four concepts + the engine absorb the entire surface. The one
net-new primitive, `delegate`, is built and proven (fan-out under a quota + join,
recorded as a connected provenance subgraph) — the same falsification bar every
shipped capability met. The residual 0.1: `research`'s composition is unproven
until built.
