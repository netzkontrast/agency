---
slug: spec-capability-and-aspects
type: spec
status: ready
summary: Capability & aspects — lazy-domaining over the four domains. A capability is authored in ONE home domain and expressed across who/how/when/where as isomorphic aspects, each materialized lazily only when needed, owned by the holding domain. No eager 4x triplication. jules (home who) is the minimal proof.
---

# Capability & aspects (lazy-domaining)

> **Status: specced — not built (except where noted).** `jules` (home `who`,
> one authored aspect, the rest lazy) is the MINIMAL committed proof.

## Concept

A **capability** (jules, music, novel, meta-development) is a vertical area of
work. It is **authored in exactly one home domain** — its primary concern — and
expressed across the four domains as **aspects**:

- its **who aspect** — sessions / dispatch,
- its **how aspect** — craft verbs,
- its **when aspect** — task state machine,
- its **where aspect** — memory.

The aspects are the SAME capability faithfully restated per domain — they are
**isomorphic** restatements, not separate features.

## Lazy-domaining

A capability materializes an aspect in a non-home domain **only when it needs
one**.

- **Default = lazy graph data**: a when aspect appears as `Task` / gate nodes
  the moment process state is first needed; a where aspect appears as
  `Artefact` / memory nodes the moment the capability first produces or learns;
  a how aspect appears the moment a craft verb is first published. No authored
  folder is required.
- A capability with **fixed structure** may instead **author** an aspect,
  following the home domain's canonical aspect shape.
- Authored or lazy, **the holding domain owns the aspect**.

There is **no eager 4× triplication** and no forced isomorphism beyond what a
capability actually needs.

## Home placement

| Primary concern | Home domain |
|---|---|
| orchestration / actor lifecycle | `who` |
| craft / actions | `how` |
| multi-step process | `when` |
| data / memory | `where` |

## The minimal proof — `jules` (home `who`)

| Aspect | Status |
|---|---|
| who (home) | **authored** — dispatch/handoff/release + poll/roster/verify + orchestration verbs |
| how | **lazy** — until `how.jules.patch` / `bulk` is first needed |
| when | **lazy** — the task state machine (investigate→patch→verify→pr; gate tests-green; silent-fail recovery) |
| where | **lazy** — sessions / patches / lessons as nodes |

One authored aspect, the rest lazy — this is lazy-domaining end to end, with no
eager folders for the other three domains.

## Naming

Every aspect's verbs derive from `(domain, capability, verb)`:
`mcp__<domain>_<capability>_<verb>` · `/agency:<domain>:<capability>:<verb>` ·
`domain.capability.verb()`.

## Interactions

- A capability's who aspect dispatches sessions that `DRIVES` its when-task and
  `record`s into its where aspect — the four aspects compose as one trip (see
  [EXAMPLE.md](../EXAMPLE.md)).
- Cross-capability work: one capability's `who.dispatch(role=other)` spawns
  another (e.g. `meta-development` dispatching `jules`).
