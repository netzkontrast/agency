---
slug: extension-plan
type: roadmap
status: draft
summary: DRAFT — the comprehensive plan for growing the agency engine by extension. The recipe (drop a CapabilityBase file that owns its ontology fragment), the built capabilities, the planned capability surface (from the capability roadmap) each mapped to what it adds + its CORE mapping + dependencies, a phased build order, and the cross-cutting engine work. Every item is an additive extension; the core stays small.
---

# Extension plan (draft)

How the agency engine grows: **by extension, not by editing the core.** Each new
capability is a file dropped into `agency/capabilities/` that the engine discovers
by reflection and auto-wires; it owns its ontology fragment; it reaches every
service through one `CapabilityContext`. The core stays domain-agnostic.

## The extension recipe

1. **Add a file** `agency/capabilities/<name>.py` with a `CapabilityBase` subclass:
   `name`, `home`, an `OntologyExtension` (`nodes` · `edges` · `enums` · `skills` ·
   `schemas` · `templates` — see [specs/capability-base.md](vision/specs/capability-base.md)),
   and `@verb(role=…)` methods that use `self.ctx`.
2. **Reach services via `ctx`** — `ctx.memory`, `ctx.ontology`, `ctx.render` /
   `ctx.schema` / `ctx.validate`, `ctx.call` / `ctx.spawn` (delegate to siblings),
   `ctx.intent_id`, `ctx.client`. No string-keyed injection.
3. **Own your schemata** — node types, enums, skills, and template-schemas ride in
   the capability's `OntologyExtension`, merged strictly onto the core.
4. **Stay CORE-faithful** — verbs are role-tagged `act`/`transform`/`effect`;
   code-mode stays the only public contract; every call records an Invocation that
   `SERVES` the intent; never reintroduce a dropped idea (four-verb surface, fixed
   domains, manifest.toml).
5. **Prove it** — a complete-implementation test (a real walk / real provenance),
   then `python -m agency.install` to refresh the self-hosted install.

## Built (v0.1 + this branch)

| Capability | Role(s) | Adds (ontology) | Status |
|---|---|---|---|
| `plugin` | act/transform | `Plugin`,`Command` nodes; skill/manifest/command/marketplace template-schemas; `skill-creation`,`plugin-dev` skills | built |
| `develop` | transform | 7 dev-discipline skills (brainstorm·plan·tdd·debug·verify·spec-panel·review) | built |
| `reflect` | act/transform | `Reflection` node + `scope` enum + `OBSERVED_DURING` edge | built |
| `jules` | effect/transform | (core types) — the first delegation driver | built |
| `music` | act | `Album`/`Track` nodes + `album type` enum + `album-concept` skill | built |
| `delegate` | effect/transform | `Delegation` node + `DELEGATES_TO`/`REDUCES_INTO` edges; fan-out+quota+join on `ctx.spawn` | built |

## Planned capability surface

Each is an additive extension; ordering reflects dependencies. (Cluster detail:
[vision/CAPABILITY-CLUSTERS.md](vision/CAPABILITY-CLUSTERS.md).)

| Capability | Role(s) | Adds | CORE mapping | Depends on |
|---|---|---|---|---|
| `gate` | transform | a reusable precondition/quality predicate verb; `GATED_BY` edge; evidence node | Lifecycle gate as a callable check | — |
| `research` | agent/transform | a lead+specialists fan-out + a verifier gate; `CITES`/`VERIFIED_BY` edges | composition: `delegate` → craft → `gate` | delegate, gate |
| `reflect+` (semantic recall) | transform | vector-ranked `recall` over `Reflection` | Memory read projection | reflect |
| `navigate` | transform | `status`/`next` read-projections over Lifecycle+Memory vs. acceptance | `project` / `provenance` views | — |
| `craft` packs | act | domain artefact generators (e.g. more `music`/novel verbs) | open `act` set + templates | — |
| `effect` packs | effect | git / fs / cloud side-effects with before/after evidence | open `effect` set | — |
| more drivers | agent | local-subagent / other-worker drivers for `delegate` | `delegate` driver slot | delegate |

## Phased build order

- **Phase A (now):** `delegate` ✅. Then `gate` (extract the hard-gate predicate so
  any phase/verb can call it) and lift jules `verify` to a `delegate` join-gate.
- **Phase B:** `research` as a skill template composing `delegate`+`gate`; a second
  `delegate` driver (local subagent) to prove the driver seam.
- **Phase C:** `navigate` read-projections; `reflect` semantic recall.
- **Phase D:** domain `craft`/`effect` packs (music/novel bundles) as separate
  capability files.

## Cross-cutting engine work (not capabilities)

- **Loop-detection middleware** — generalize the `ctx.spawn` depth guard into an
  engine-level guard (CORE names it as middleware).
- **Result envelope (opt-in)** — a `ctx` helper for `ok/data/warnings/…` if/when a
  uniform envelope earns its keep; not mandatory (would bloat code-mode deltas).
- **A2A boundary adapter** — expose/consume external agents over the A2A protocol,
  reusing the `delegate` model.
- **Schema→inputSchema glue** — make a capability's `schema(name)` the single source
  for the MCP `inputSchema` (today FastMCP derives it from the verb signature).

> Draft. Sequencing and scope are subject to the design loop (brainstorm →
> research → design → spec-panel → review) before each capability lands.
