# agency

A Claude Code plugin: **ONE FastMCP engine + ONE GraphQLite graph** that hosts
everything an agent does. Its design is the **5W1H decomposition** of any unit
of work.

The human owns **Why / What** — the **INTENT**. The engine executes the other
four as **four isomorphic domains**:

- **who** — the agent-session lifecycle: which actor performs the work
  (dispatch, handoff, supervision, harness-in-harness).
- **how** — the craft: skills, tools, actions. An OPEN domain of
  capability-specific verbs, discoverable through a mandatory
  `how.<capability>.help`.
- **when** — the task / process lifecycle: order, gates, scheduling, triggers.
- **where** — memory: a bi-temporal, append-only GraphQLite graph plus
  artefacts.

INTENT is the human's root, captured via `why.capture` → `why.confirm` and
pinned once as an **Intent node**; every action edges back to it via
`SERVES_INTENT`.

The three closed domains (who / when / where) share **one two-axis canonical
verb frame** — Lifecycle (`open · move · close`) and Observe (`read · find ·
check`, plus `watch`). `how` is open: each capability verb is TAGGED with the
frame role it fills.

A **capability** (jules, music, novel, meta-development) is a vertical area of
work. It is authored in exactly ONE **home domain** and expressed across the
four as **aspects**, each materialized **lazily** only when needed
(**lazy-domaining**). No eager 4× triplication.

## Status — full concept, minimal proof

This repo, at this stage, **is** the Concept, the Vision canon, and the Plan.
Everything is **documentation**. The Vision DOCUMENTS the entire four-domain
model; the buildable/committed slice is deliberately MINIMAL: the `jules`
capability anchored in `who`, with one authored aspect and the rest lazy, plus
one worked example. Everything else is marked **"specced — not built."** No
code is implemented here; do not read these docs as shipped behavior.

**Start here:** [`CLAUDE.md`](CLAUDE.md) for how to work in this repo, then
[`docs/vision/`](docs/vision/README.md) for the authoritative design canon. The
Vision is authoritative: where any prototype diverges from the canon, the canon
wins.
