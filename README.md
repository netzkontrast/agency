# agency

A Claude Code plugin: a three-domain engine for agent workflows. It exposes
exactly three base domains — `agentic` (skills, tools, orchestration),
`workflow` (process), and `context` (graph, schemas) — over one FastMCP engine
backed by a GraphQLite graph. Capabilities are added as rows nested in their
owning domain; `jules` (async-coding orchestration) is the first.

**Start here:** [`CLAUDE.md`](CLAUDE.md) for how to work in this repo, then
[`docs/vision/`](docs/vision/README.md) for the authoritative design canon.
