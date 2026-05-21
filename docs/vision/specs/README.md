---
slug: specs-index
type: spec-index
status: ready
summary: The contracts implementation must satisfy. Read OVERVIEW.md and ARCHITECTURE.md first.
---

# Specs — the contracts

Each spec is the authoritative contract for one part of the system. Read
`../OVERVIEW.md` (the model) and `../ARCHITECTURE.md` (the runtime) first.

| # | Spec | Owns |
|---|---|---|
| 01 | [manifest](01-manifest.md) | the row manifest + name derivation |
| 02 | [tool-result-envelope](02-tool-result-envelope.md) | the frozen tool return shape |
| 03 | [gate](03-gate.md) | gate definition + evaluator contract |
| 04 | [agentic-base](04-agentic-base.md) | harness: four-verb contract, discovery, CodeMode |
| 05 | [workflow-base](05-workflow-base.md) | runner: graph walk, gates, continuation |
| 06 | [context-base](06-context-base.md) | store: graph, drivers, hooks, Artefact node |
