---
slug: roadmap
type: roadmap
status: ready
summary: Roadmap for the agency plugin (v4). v0.1 ships an installable Claude Code plugin — the engine, three capabilities (plugin/jules/reflect), reflection-based self-registration, an extensible capability-owned ontology, and a self-hosted install. Next: the delegate capability, the deferred hardening items, and broader capability bundles.
---

# Roadmap

The canon in `docs/vision/` defines the **v4 four-concept model** (see
[CORE.md](vision/CORE.md)); the survey/cluster/spec-panel of every installed
plugin is in [CAPABILITY-CLUSTERS.md](vision/CAPABILITY-CLUSTERS.md). This file
tracks the plan.

## v0.1 — DONE: the installable plugin (19/19 green)

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
- the **plugin-development capability** (skill-creation + plugin authoring,
  skill creation + plugin authoring) and **`reflect`** (durable cross-session memory);
- a **self-hosted install** the engine generates and validates for itself;
- a **vendored Jules backend** (httpx) — no external orchestrator dependency;
- the **`delegate` capability** — agent fan-out + quota + join on `ctx.spawn`
  (`DELEGATES_TO`/`REDUCES_INTO`), with `jules` as its first driver;
- a **CapabilityContext + CapabilityBase** — one typed handle per invocation; all
  five capabilities authored in the class form.

## Next

The comprehensive growth plan is **[EXTENSION-PLAN.md](EXTENSION-PLAN.md)** (draft).
Near-term:

1. **`gate`** — extract the hard-gate predicate as a callable check; lift jules
   `verify` to a `delegate` join-gate.
2. **`research`** — a skill template composing `delegate` + `gate`; add a second
   `delegate` driver (local subagent) to prove the driver seam.
3. **Deferred bi-temporal hardening** — refuse `supersede` on closed versions;
   enum enforcement in the skill walker.
4. **Domain bundles** — music/novel `craft`/`effect` packs as separate capability
   files (each owning its ontology fragment).

## Later

- Loop-detection middleware (generalize the `ctx.spawn` depth guard); an
  alternative graph driver for larger deployments; the A2A boundary adapter.
