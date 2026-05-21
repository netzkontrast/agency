---
slug: roadmap
type: roadmap
status: ready
summary: Build milestones for the agency plugin. The canon (docs/vision/) defines the model; this tracks what is built and what comes next.
---

# Roadmap

The canon in `docs/vision/` defines the model. This file tracks milestones.

## M1 — Engine + first row (current)

- `agentic` harness: four-verb contract, domain/row discovery, name derivation,
  CodeMode rendering, cold-boot under the token budget.
- `workflow` runner: graph-path walking, gate evaluation, `Continuation` nodes.
- `context`: GraphQLite store, pre/post-tool hooks, artefact-driver protocol +
  `fs` driver, runtime schemas.
- `jules` agentic row: the async-coding orchestrator (lifecycle, patches, bulk,
  source, trim, aliases) exposed as `mcp__agentic_jules_*` + `/agentic:jules:*`.

## M2 — Harden the jules row

- Express the research process via the `workflow` engine (graph phases) instead
  of a stub; replace the placeholder gate with real completion logic.
- Phase-node seeding so a hand-authored row runs end to end.

## M3 — Reach & storage

- Driver registry beyond `fs`: `repo`, `s3`, `http`, `drive`.
- Cross-row dispatch: one agentic row dispatching into another via the
  four-verb contract, recorded as a graph edge.

## Later

- Additional rows, each placed by primary concern.
- Hot-reload of skills; an alternative graph driver for larger deployments.
