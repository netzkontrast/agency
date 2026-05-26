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
- a **vendored Jules backend** (httpx) — no external orchestrator dependency.

## Next

1. **`delegate` capability** — agent fan-out + quota + join (the other net-new
   spec from the cluster panel). `jules` is the single-child reference; `delegate`
   generalizes to N children with a join/reduce gate. New edges `DELEGATES_TO`,
   `REDUCES_INTO`.
2. **Deferred bi-temporal hardening** (from PR review): provenance follows the
   `SUPERSEDED_BY` chain after `amend`; refuse `supersede` on closed versions;
   enum enforcement in the skill walker; blocked-gate provenance.
3. **Broaden the capability set** — port more crafts as their own capability
   files (each self-registering, each owning its ontology fragment). Music and
   novel become capability bundles, not core.

## Later

- Hot-reload of capabilities; an alternative graph driver for larger
  deployments; the A2A boundary adapter for external agents.
