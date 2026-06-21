# Vision Review — Spec 002 (`Boundary` / `Driver` / `DriverRegistry`)

> Reviewer: vision-alignment panel (Fowler/Newman/Nygard lenses).
> Canon: `docs/vision/CORE.md`, `docs/vision/CAPABILITY-CLUSTERS.md`,
> `docs/vision/specs/engine.md`, `docs/vision/specs/capability.md`.
> Code: `agency/capability.py`, `agency/engine.py`,
> `agency/capabilities/{jules,_vcs,delegate,subagent}.py`.

## Alignment verdict

**ALIGNED IN MECHANISM, UNDER-FRAMED IN LANGUAGE — approve with must-changes.**

The mechanism the spec builds is the right one and lands in the right place: a
generalization of the existing per-capability injector seams
(`injectors["client"]`, `injectors["vcs"]` — `engine.py:55-56`) into one named
table on `CapabilityContext`, injected by `Registry.invoke` exactly like
`client`/`memory`/`intent_id` (`capability.py:152-163`). That *is* the
`wire-handlers` cluster — **"the substrate … the engine itself"**
(CAPABILITY-CLUSTERS.md:24). It self-registers nothing, declares no verbs, emits
no MCP tool, and never enters `discover()`. It is correctly engine substrate, not
a fifth concept and not a top-level capability.

The gap is that the spec proves this by accident rather than by assertion: it
grounds every decision in `FINDINGS.md`/`PROPOSAL.md` and the vendored
`the-agency-system`, and **never once cites `CORE.md` or `CAPABILITY-CLUSTERS.md`.**
A spec that introduces two new nouns (`Boundary`, `Driver`) into a four-concept
canon must explicitly demote them to substrate vocabulary, or a future reader
will mistake `Driver` for a sibling of Intent/Capability/Lifecycle/Memory — the
exact bloat CLUSTERS:26-43 forbids.

## Canon citations

- **`wire-handlers` = the engine itself** — CAPABILITY-CLUSTERS.md:24
  (`| wire-handlers | Engine | Engine · Memory | the substrate: reflection-based
  discovery + auto-wiring, the extensible ontology | the engine itself |`). The
  registry belongs to this row. It is the injector/auto-wire plumbing, not a new
  cluster.
- **"why so few primitives" / no concept multiplication** — CAPABILITY-CLUSTERS.md:26-43,
  esp. :30-31 ("Multiplying concepts would re-introduce bloat") and :39 (~0.9
  that the four concepts + engine absorb the entire surface). `Boundary`/`Driver`
  must be framed as facets of the substrate, never as additions to the count.
- **Four concepts + one substrate; engine adds no concept vocabulary** —
  CORE.md:7-18; `specs/engine.md:16-20` ("Capabilities and concepts are data the
  Engine serves; the Engine itself adds no concept vocabulary"). A registry of
  injected boundaries is engine plumbing, consistent with this.
- **`inject` convention is the existing substrate seam** — `specs/engine.md:45-47`
  ("Params a verb declares in its `inject` list … are supplied by the Registry,
  not the caller, and are hidden from the tool's schema"); code at
  `capability.py:84-90,103,149-163`. The spec's D-2 (keep `inject=["vcs"]` as
  registry-backed sugar) is therefore canon-faithful: it extends this seam, does
  not replace it.
- **Code-mode IS the contract; `CapabilityContext` is internal, not a surface** —
  CORE.md:10-18; `specs/engine.md:22-39`; and `capability.py:37-39`
  ("A DELEGATOR over the engine's services — never a new public surface. Code-mode
  stays the only contract; this is internal"). `ctx.drivers`/`ctx.get_driver` add
  to this internal delegator and emit no new public tool — the public surface
  stays exactly `search` · `get_schema` · `execute`. Preserved.
- **Role-tag model (`act`/`transform`/`effect`)** — CORE.md:25-28;
  `specs/capability.md:14-28`. Drivers sit *behind* `effect`/`transform` verbs
  (`jules.dispatch` is `effect`; `workspace.isolate` is `effect`); they expose no
  new role and no new public verb. Preserved.
- **Every `call_tool` records an Invocation (the provenance moat)** — CORE.md:53-54
  ("because every `call_tool` records an Invocation, it mirrors itself into the
  provenance graph"); CORE.md:38-45 (cross-concern provenance is one traversal);
  enforced at `capability.py:164-180` (Invocation recorded before the call).
  This is the canon basis for the `fan_out` carve-out below.

## Misalignments

### M1 — No canon citation; "engine substrate, not concept" is never asserted (MAJOR)
The spec's "Why" cites `FINDINGS.md:16`, `PROPOSAL.md §2`, ADR-0004, and the
vendored MCP server — but never `CORE.md` or `CAPABILITY-CLUSTERS.md`. The
`CLAUDE.md` rule is explicit: "The canon wins; code serves it" and "Keep
`docs/vision/` authoritative." A substrate spec that introduces new nouns without
anchoring them to the `wire-handlers` row and the four-concept model risks a
future reader treating `Driver` as a fifth primitive. **The framing is correct in
fact but absent in words.**

### M2 — `Boundary`/`Driver` are new vocabulary the canon does not use (MODERATE)
The canon's word for these seams is *injectors* / *boundaries behind `inject`*
(`specs/engine.md:45-47`; `capability.py:129-132`). Adding `Boundary` and `Driver`
as named Protocols is acceptable *as an implementation detail of the substrate*,
but the spec must say so loudly, or the names read as concept-level. The existing
code already calls these "boundary objects" in comments (`capability.py:45`,
`engine.py:41-42,53`) — the spec should adopt that framing verbatim and state
that `DriverRegistry` is the generalization of `Registry.injectors`, full stop.

### M3 — `Driver` marker carries an optional introspection member — soft drift (MINOR)
"Done When" item 1 says `Driver` "carries one optional introspection member
(`name`/`describe()`)", while the Design block (and D-6) correctly insist the
marker has **no** members (PEP 544 no-op `isinstance`, and a required member would
force a behaviour change onto `JulesClient`/`GitClient` that the spec forbids).
These two statements contradict. The Design block is the canon-correct one (a
dumb I/O edge, no contract beyond the wrapping capability's `ToolResult`). Delete
the "introspection member" clause from item 1. A registry whose marker has no
members and that is *not* `isinstance`-gated is the honest substrate shape.

### M4 — `fan_out` provenance: correctly carved out, but the deferral must cite CORE (CONFIRMED-OK, tighten wording)
The spec's treatment of `delegate.fan_out` is the strongest, most canon-faithful
part and should be preserved. Grounding confirmed against code:
`delegate.fan_out(driver, driver_verb, …)` means **capability name + verb**,
dispatched through `ctx.spawn` (`delegate.py:29,40,52`), and `subagent.develop`
calls it with `driver="jules", driver_verb="dispatch"` (`subagent.py:23-28,27`).
`ctx.spawn` → `Registry.invoke` records an Invocation and links it `SERVES`
(`capability.py:54-55,164-169`). A raw `DriverRegistry` `Driver.create()` flows
through **none** of that, so it records **no Invocation** — which would break
CORE.md:53-54 and the one-traversal provenance moat (CORE.md:38-45). The spec
correctly (a) keeps `delegate.py` out of `affects:`, (b) refuses to make a
registered `Driver` a delegation target, and (c) defers the rename + an
Invocation-recording dispatch path to a follow-up. **This is exactly right.** The
only fix: the deferral text (Design "OUT OF SCOPE" block + Open Q-1) cites
`delegate.py:11-12,48-54` but should *also* cite CORE.md:53-54 as the canonical
reason, so the provenance guarantee is named, not merely described.

### M5 — Two meanings of "driver" coexist in-tree during this spec (MODERATE, acknowledged)
After this spec, "driver" means both (a) a `fan_out`/`subagent` arg = capability
name (`delegate.py:29`, `subagent.py:23`) and (b) a registered `DriverRegistry`
object. The spec acknowledges this collision and defers the rename. Acceptable for
an additive spec, but the collision is a standing canon hazard (a reader cannot
tell which "driver" CORE-level provenance applies to). The follow-up rename should
be tracked as blocking before any `fan_out`↔registry integration.

## Recommended aligned framing ("engine substrate, not concept")

Add a short "Vision alignment" subsection at the top of the spec stating, in canon
vocabulary:

> **This is engine substrate, not a new concept.** `Boundary`/`Driver`/
> `DriverRegistry` are the generalization of the engine's existing injector seams
> (`Registry.injectors["client"|"vcs"]`, `engine.py:55-56`) — the `wire-handlers`
> cluster, "the engine itself" (CAPABILITY-CLUSTERS.md:24). They add **no** fifth
> concept (the four — Intent/Capability/Lifecycle/Memory — are unchanged;
> CORE.md:7-18), **no** public tool (the contract stays `search`·`get_schema`·
> `execute`; `specs/engine.md:22-39`), and **no** new role-tag (drivers sit behind
> existing `effect`/`transform` verbs; CORE.md:25-28). A `Driver` is an internal
> I/O seam reached only through `CapabilityContext` — "a DELEGATOR over the
> engine's services, never a new public surface" (`capability.py:37-39`). The
> capability that wraps a driver owns the `ToolResult` and **all** provenance
> writes; a driver records nothing itself (CORE.md:53-54 stays intact because the
> wrapping verb's `Registry.invoke` records the Invocation, `capability.py:164-169`).

Frame `DriverRegistry` explicitly as "`Registry.injectors`, generalized to a named
table" everywhere it appears.

## Must-change list

1. **(M1) Cite the canon.** Add the "Vision alignment" subsection above; cite
   CAPABILITY-CLUSTERS.md:24 (`wire-handlers` = the engine) and :26-43 (no concept
   multiplication), CORE.md:7-18 (four concepts unchanged), and
   `specs/engine.md:45-47` (`inject` is the existing seam this generalizes).
   State in words that this is substrate, not a concept and not a capability.
2. **(M3) Remove the `Driver` introspection-member clause** from "Done When" item 1
   so it agrees with the Design block + D-6: the marker has **no** members and is
   not `isinstance`-gated (PEP 544 no-op; forcing a member would break the
   "no behaviour change to `JulesClient`/`GitClient`" promise).
3. **(M4) Name the provenance guarantee in the `fan_out` deferral.** In the Design
   "OUT OF SCOPE" block and Open Q-1, add a CORE.md:53-54 citation as the canonical
   reason a raw `Driver` call is forbidden as a delegation target (every
   `call_tool`/`ctx.spawn` must record an Invocation; `capability.py:164-169`).
   Keep the carve-out and the deferral exactly as written.

### Nice-to-have (non-blocking)
- (M2) Adopt the existing in-tree word "boundary" and describe `DriverRegistry` as
  "`Registry.injectors` generalized" throughout, to keep the noun count honest.
- (M5) Track the "driver" rename as a blocker on the follow-up `fan_out`↔registry
  spec; do not integrate the two meanings until renamed.
