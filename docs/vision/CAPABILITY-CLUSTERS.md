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
| `music` (domain bundle) | act | Capability · Memory | the album conceptualizer (a 7-phase gated skill) + `Album` types | **built (v0.1)** |
| `delegate` | agent, effect | Capability · Lifecycle · Memory | spawn a child Lifecycle with a scoped Intent + budget; fan out N under a quota; join on terminal states (`DELEGATES_TO`, `REDUCES_INTO`) | **spec — next** |
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
bloat. After the collapse, exactly **two** net-new capabilities are worth specc'ing
beyond v0.1:

1. **`delegate`** — agent fan-out + quota + join. `jules` is the single-child
   reference; `delegate` generalizes to N children with a join/reduce gate.
2. **`research`** — a *composition* (delegate → craft → gate), shipped as a skill
   template rather than a primitive.

## Confidence

~0.9 that the four concepts + the engine absorb the entire surface, and that
`delegate` is the one net-new primitive worth carrying forward. The residual 0.1:
`delegate`'s join/quota semantics are unproven until built — the same
falsification bar every shipped capability met.
