# agency

A Claude Code plugin: ONE engine that hosts everything an agent does. It
exposes exactly **three domains** — `agentic` (actions: skills, tools, the
four-verb harness), `workflow` (process: graph-walking state machines), and
`context` (memory: the GraphQLite graph, schemas, drivers, hooks) — over one
FastMCP engine backed by one GraphQLite graph.

A **capability** is a vertical area of work (e.g. `jules`, `music`, `novel`).
It is authored in exactly one **home domain** (its primary concern) and
expresses itself across the domains as **aspects**: an agentic aspect, a
workflow aspect, a context aspect — the same capability faithfully restated in
each domain's language. A capability materializes an aspect in a non-home
domain only when it needs one (**lazy-domaining**); the holding domain owns it,
whether it is lazy graph data or an authored folder. `jules` (async-coding
orchestration) is the first capability, authored in `agentic`.

This repo, at this stage, **is** the Concept, the Vision canon, and the Plan.
Implementation follows on this branch. The Vision is authoritative: where
prototype code diverges from the canon, the canon wins.

**Start here:** [`CLAUDE.md`](CLAUDE.md) for how to work in this repo, then
[`docs/vision/`](docs/vision/README.md) for the authoritative design canon.
