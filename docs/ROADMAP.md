---
slug: roadmap
type: roadmap
status: ready
summary: Roadmap for the agency plugin. v0.1 ships an installable Claude Code plugin — the engine, ten core capabilities, reflection-based self-registration, an extensible capability-owned ontology, and a self-hosted install. Domain capabilities load as example extensions. Next: more delegate drivers, carrying skill references, and the A2A boundary adapter.
---

# Roadmap

The canon in `docs/vision/` defines the **four-concept model** (see
[CORE.md](vision/CORE.md)); the survey/cluster/spec-panel of every installed
plugin is in [CAPABILITY-CLUSTERS.md](vision/CAPABILITY-CLUSTERS.md). This file
tracks the plan.

## v0.1 — DONE: the installable plugin (56 passing)

v0.1 ships as an installable Claude Code plugin (this repo). Proven:

- **the moat** — cross-concern provenance in one graph traversal;
- **two genuinely different capabilities** — a synchronous craft/compute
  (`plugin`) and a remote async agent (`jules`);
- **code-mode IS the contract** (`search`/`get_schema`/`execute`), exposed
  isomorphically over MCP · Skills · a bash CLI;
- **bi-temporal Memory** (`as_of`); **`COMPLETED ≠ done`** (`verify`);
- **capabilities self-register by reflection** and auto-wire (add a file);
- an **extensible, capability-owned ontology** (core + per-capability extensions,
  merged strictly, enforced in Memory);
- the **plugin-development capability** (skill-creation + plugin authoring) and
  **`reflect`** (durable cross-session memory);
- the **development disciplines** (`develop`: brainstorm · plan · tdd · debug ·
  verify · spec-panel · review · execute) as walkable, gated skills;
- **orchestration** — `delegate` (fan-out + quota + join on `ctx.spawn`),
  `subagent` (subagent-driven development), and `gate` (a reusable hard-gate);
- **dev-workflow VCS** — `workspace` (isolate + baseline) and `branch` (assess +
  finish) over an injected VCS boundary;
- a **self-hosted install** the engine generates and validates for itself;
- a **vendored Jules backend** (httpx) — no external orchestrator dependency;
- a **CapabilityContext + CapabilityBase** — one typed handle per invocation; every
  capability authored in the class form;
- domain capabilities load **out of core** as example extensions (`examples/`),
  via `Engine(extra_capabilities=…)`.

## Next

The comprehensive growth plan is **[EXTENSION-PLAN.md](EXTENSION-PLAN.md)** (draft).
Near-term:

1. **More `delegate` drivers** — beyond `jules` and a local subagent, prove the
   driver seam against another backend.
2. **Carry skill references** — bring the heavy how-to files as on-demand
   capability references (`develop.reference`), loaded only when needed.
3. **The A2A boundary adapter** — expose the Lifecycle state machine over A2A.
4. **More domain bundles** — additional example extensions (novels, …), each
   owning its ontology fragment.

## Later

- Loop-detection middleware (generalize the `ctx.spawn` depth guard); an
  alternative graph driver for larger deployments.
