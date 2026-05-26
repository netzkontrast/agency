---
slug: vision-overview
type: vision
status: ready
summary: The v2.1 model — one engine, one graph, designed as the 5W1H decomposition of work. The human owns Why/What = INTENT; the engine executes who/how/when/where as four isomorphic domains sharing a two-axis canonical verb frame. Capabilities are authored in one home domain and expressed across the four as aspects, materialized lazily. Names self-describe.
---

# Overview — intent + four domains (5W1H)

The agency plugin is ONE Claude Code plugin: **ONE FastMCP engine** backed by
**ONE GraphQLite graph**. Its design is the **5W1H decomposition** of any unit
of work — who, what, when, where, why, how. The human owns **Why / What**; the
engine owns the other four.

## INTENT — the human's root (why / what)

The human owns **Why / What = INTENT**: the reason the work exists and what
"done" means. Intent is captured via `why.capture` → `why.confirm` and
persisted as a single **Intent node**, **pinned once** and thereafter
referenced by node-id (cache-safe — the text is never re-pasted). Every action
the engine takes edges back to it via a `SERVES_INTENT` edge.

Intent is its **own root**, distinct from `where`'s execution memory: `where`
remembers what happened; the Intent node remembers why it was supposed to
happen. See [specs/intent.md](specs/intent.md).

## The four domains

- **who** — the agent-**session** lifecycle. Which actor performs the work:
  dispatch, handoff, supervision, harness-in-harness. See [specs/who.md](specs/who.md).
- **how** — the **craft**: skills, tools, actions. An OPEN domain of
  capability-specific verbs, discoverable through a mandatory
  `how.<capability>.help`. See [specs/how.md](specs/how.md).
- **when** — the **task / process** lifecycle: order, gates, scheduling,
  triggers. See [specs/when.md](specs/when.md).
- **where** — **memory**: a bi-temporal, append-only GraphQLite graph plus
  artefacts. See [specs/where.md](specs/where.md).

The four are **isomorphic domains** — each is a lens on the same work, not a
layer stacked on the others.

### who ↔ when boundary

`when` owns the **TASK** lifecycle (the process and its gates); `who` owns the
**AGENT-SESSION** lifecycle (the actor doing the work). A `DRIVES` edge links a
who-session to the when-task it advances. State is **never duplicated** across
them: a session's progress lives in `who`; a task's phase/gate state lives in
`when`; the `DRIVES` edge is the join.

## The two-axis canonical verb frame

The three **closed** domains (who / when / where) share ONE verb frame. Every
function maps to exactly one axis:

- **Lifecycle** (write): `open · move · close`
- **Observe** (read): `read · find · check` (plus `watch` for live / subscribe)

| Domain | open | move | close | read | find | check |
|---|---|---|---|---|---|---|
| **who** | dispatch | handoff | release | poll | roster | verify |
| **when** | start | advance | complete | status | list | check (gate) |
| **where** | record | link | supersede | recall | find | validate |

`how` is the **OPEN** domain: its verbs are capability-specific (music:
`write` / `master` / `mix`; jules: `patch` / `bulk`), and each is **TAGGED**
with the frame role it fills. A specialist verb is allowed to live in any
closed domain, but it MUST declare its frame role, and that role is surfaced as
a call-site **ALIAS** — e.g. `where.music.supersede` ≡ `where.music.close`. The
frame is the spine; specialist names are skins over it.

## Capabilities express themselves as aspects

A **capability** is a vertical area of work — e.g. `jules`, `music`, `novel`,
`meta-development`. It is **authored in exactly one home domain** (its primary
concern) and expresses itself across the four domains as **aspects**: a who
aspect, a how aspect, a when aspect, a where aspect. The aspects are the SAME
capability faithfully restated in each domain's language — they are
**isomorphic**.

### Lazy-domaining

A capability materializes an aspect in a non-home domain **only when it needs
one** — **lazy-domaining**.

- The default is **lazy graph data**: a when aspect appears as `Task` / gate
  nodes the moment the capability first needs process state; a where aspect
  appears as `Artefact` / memory nodes the moment it first produces or learns.
  No authored folder is required.
- A capability with **fixed structure** may instead **author** an aspect.
- Authored or lazy, **the holding domain owns the aspect**.

There is **no eager 4× triplication** and no forced isomorphism beyond what a
capability actually needs. See [specs/capability-and-aspects.md](specs/capability-and-aspects.md).

## Naming (self-describing)

Every public name derives from `(domain, capability, verb)`:

- MCP tool: `mcp__<domain>_<capability>_<verb>` — e.g. `mcp__who_jules_dispatch`.
- Skill: `/agency:<domain>:<capability>:<verb>` — e.g. `/agency:how:jules:patch`.
- code-mode: `domain.capability.verb()` — e.g. `where.jules.record(...)`.

The name alone tells you the domain, the capability, and the verb.

## The stress test (proves the model)

- **`jules`** (home `who`): the async-coding orchestrator. Who aspect authored
  (dispatch / handoff / release + poll / verify, plus the orchestration verbs);
  how aspect lazy until its first specialist verb (`how.jules.patch`); when
  aspect lazy (the task state machine, incl. silent-fail recovery —
  `COMPLETED` ≠ done); where aspect lazy (sessions / patches / lessons). One
  authored aspect. **This is the minimal proof.**
- **`music`** (home `how`, specced — not built): heavy craft (write / master /
  mix), authoring across domains; the "fully-domained" extreme proving home ≠
  exclusive ownership.
- **`meta-development`** (home `who`, specced — not built): the system improving
  itself; its where aspect is the system's own graph (reflexive); it dispatches
  `jules` via `who.dispatch`.

## Scope

The Vision DOCUMENTS this entire four-domain model. The buildable/committed
slice is MINIMAL — `jules` in `who`, one authored aspect, the rest lazy, plus
the worked example. Everything else is **"specced — not built."** This repo is
documentation; no code is implemented here.
