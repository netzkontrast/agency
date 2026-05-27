# Agency documentation

**Agency** is an installable Claude Code plugin and a small engine for building
agentic systems on one idea: *everything an agent does is a node in one
provenance graph, and code-mode is the only contract.*

This folder has two halves — **guides for humans** (start here) and the
**design canon** (the authoritative model, for contributors).

## Guides (for humans)

| Guide | Read it to… |
|---|---|
| [getting-started.md](getting-started.md) | install, run the tests, and make your first call |
| [guide/concepts.md](guide/concepts.md) | understand the model in plain language (the four concepts + the engine) |
| [guide/usage.md](guide/usage.md) | drive the engine — code-mode, context-mode, and the three surfaces (CLI · MCP · Skills) |
| [guide/capabilities.md](guide/capabilities.md) | the capability reference — what ships and every verb |
| [guide/extending.md](guide/extending.md) | add your own capability (and the `examples/` extension point) |

## Design canon (for contributors)

The authoritative model lives in [vision/](vision/) — read
[vision/CORE.md](vision/CORE.md) first, then `OVERVIEW.md` and `ARCHITECTURE.md`.
Per-part contracts are in [vision/specs/](vision/specs/). The canon is
authoritative; the code serves it.

- [ROADMAP.md](ROADMAP.md) — where this is going.
- [EXTENSION-PLAN.md](EXTENSION-PLAN.md) — the capability-extension recipe + surface.
- [examples/](examples/) — runnable walkthroughs.

> Version: **v0.1**. Early, but real: capabilities self-register by reflection,
> and the engine authors and validates its own plugin install.
