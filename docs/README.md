# Agency documentation

**Agency** is an installable Claude Code plugin and a small engine for building
agentic systems on one idea: *everything an agent does is a node in one
provenance graph, and code-mode is the only contract.*

This folder is organised in four layers — pick your depth:

| Layer | Folder | For… |
|---|---|---|
| **Guides** | [guide/](guide/) + [getting-started.md](getting-started.md) | humans driving the engine (start here) |
| **Architecture** | [architecture/](architecture/) | contributors — how it's built, module by module |
| **Specs** | [specs/](specs/) | the spec system + the binding status index |
| **Operations** | [operations/](operations/) | dev loop, testing, CI, the two drift gates |
| **Vision (canon)** | [vision/](vision/) | the authoritative model — *why* it's shaped this way |

## Guides (for humans)

| Guide | Read it to… |
|---|---|
| [getting-started.md](getting-started.md) | install, run the tests, and make your first call |
| [guide/concepts.md](guide/concepts.md) | understand the model in plain language (the four concepts + the engine) |
| [guide/usage.md](guide/usage.md) | drive the engine — code-mode, context-mode, and the three surfaces (CLI · MCP · Skills) |
| [guide/capabilities.md](guide/capabilities.md) | the capability reference — every capability + verb (**generated** from the live registry) |
| [guide/extending.md](guide/extending.md) | add your own capability (and the `examples/` extension point) |

## Architecture (engineering reference)

[architecture/](architecture/) documents the engine module by module —
[overview.md](architecture/overview.md) (the four concepts, the wire contract, the
bootstrap flow) then one page per part: engine · capability-system · ontology · memory ·
intent/lifecycle/gate · toolresult · skills · drivers · token-economy · install/cli ·
helpers. Each page carries a **doc-drift marker** naming the source it documents.

## Design canon (for contributors)

The authoritative model lives in [vision/](vision/) — read
[vision/CORE.md](vision/CORE.md) first, then `OVERVIEW.md` and `ARCHITECTURE.md`.
Per-part contracts are in [vision/specs/](vision/specs/). The canon is
authoritative; the code serves it.

- [specs/](specs/) — the spec system; [/TODO.md](../TODO.md) is the binding index.
- [operations/](operations/) — dev/test/CI + the **drift gates** (`check-drift`,
  `check-doc-drift`).
- [ROADMAP.md](ROADMAP.md) — where this is going.
- [EXTENSION-PLAN.md](EXTENSION-PLAN.md) — the capability-extension recipe + surface.
- [examples/](examples/) — runnable walkthroughs.

## Keeping these docs honest

Hand-written docs declare the code/specs they describe via a `doc-source` marker (an
HTML comment naming the source files); `scripts/check-doc-drift` flags any doc whose
sources changed since it was stamped, and `scripts/gen-capability-docs` regenerates the
capability reference from the live registry. So "complete" stays true — see
[operations/](operations/).

> Version: **v0.1**. Early, but real: capabilities self-register by reflection,
> and the engine authors and validates its own plugin install.

<!-- doc-source: agency/engine.py agency/capability.py -->
<!-- doc-hash: 0daa521f8ee24cb0 -->
