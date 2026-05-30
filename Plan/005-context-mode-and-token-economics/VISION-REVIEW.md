# VISION-REVIEW — Spec 005 (Context Mode, output-side & Token Economics)

> Vision-alignment review against the canon (`docs/vision/CORE.md`,
> `CAPABILITY-CLUSTERS.md`, `docs/vision/specs/engine.md`) and the running code
> (`agency/engine.py`, `capability.py`, `capabilities/*`). Spec-panel-style
> critique (Fowler / Newman / Nygard / Hohpe on architecture-fidelity; Wiegers on
> testable boundaries), focused on the mechanism-vs-concept line the canon draws.

## Alignment verdict

**CONDITIONAL — REFRAME REQUIRED (not reject).** The *problem* the spec attacks is
real and canon-blessed (token economy is a first-class engine virtue —
`engine.md:50-55`, `CORE.md:11-13,42`). But the spec's chosen *shape* crosses the
canon's sharpest line in two places at once:

1. it promotes a **cross-cutting guard (output capture / compaction)** to a
   **first-class `ContextCapability`** — the exact inversion CORE.md:16-18 forbids;
2. it ships a **Claude-Code hook layer** that the plan-of-record explicitly puts
   **out of scope for v1** (`Plan/000-overview.md:96-98`).

The deferral discipline inside the spec (no `PreCompact`, no checkpoint/restore,
no event taxonomy) is genuinely good and canon-honest. The remaining misalignment
is structural, not scope: *what is a concept vs. what is middleware.* Fix the
framing and most of the spec survives.

## Canon citations (the load-bearing lines)

- **CORE.md:16-18** — *"Cross-cutting guards (quality-score, loop-detection,
  **compaction**, `Slot`/quota) are engine **middleware, not concepts.**"* This is
  the central ruling line. Output-side capture that replaces a large tool output
  with a summary + handle **is compaction** by the canon's own naming. The canon
  has already classified this family: middleware.
- **engine.md:67-74** — the guards table lists **"compaction checkpoint — named
  checkpoint that prunes working context; full record stays in Memory."** That is
  *precisely* this spec's mechanism (prune the big output from context; keep the
  full body in a store). The canon already owns this slot — as a guard, not a
  capability.
- **CORE.md:9-18 / engine.md:16-34** — *"Code-mode IS the contract … the public
  surface is exactly `search` · `get_schema` · `execute` … intermediate results
  stay in-sandbox, only deltas cross."* This is the **schema-side AND the
  in-sandbox token story already.** The spec's own §Design concedes the boot win is
  banked here. The output-side story must compose *with* this contract, not erect a
  parallel one.
- **CORE.md:25-28 / CAPABILITY-CLUSTERS.md:20,24** — a Capability is *"an invokable
  action"* whose verbs are role-tagged craft. `transmute` (*"views, indexes,
  summaries, tool-list shaping"*) is named as **the open `transform` set — a facet,
  not a primitive**, and `wire-handlers` is **"the engine itself."** A
  search-an-index-and-summarize surface is textbook `transmute`/`wire-handlers`
  territory, i.e. a facet/the engine — never a new top-level concept.
- **CAPABILITY-CLUSTERS.md:26-33** — *"Most clusters are facets of the four
  concepts, not new top-level primitives … Multiplying concepts would re-introduce
  bloat."* The only sanctioned net-new primitives were `delegate` (built) and
  `research` (a composition). Context-mode is not on that list.
- **Plan/000-overview.md:96-98** — *"Hook layer → **out of scope for v1**:
  loop-detection ships as a pure verb, context-mode snapshot/restore is deferred …
  **no hook layer is built yet.**"* Spec 005 ships `hooks/hooks.json` + four hook
  handlers — direct collision with the plan's own resolved decision.

## The capability-vs-middleware ruling

**RULING: This is engine MIDDLEWARE, with a thin TRANSFORM facet for the read
path — NOT a new first-class `ContextCapability`.** Specifically a two-part split:

1. **Output capture / summarize-on-overflow = engine middleware (a guard).** The
   PostToolUse-style "if output > threshold, store body, return summary + handle"
   step is *compaction*. CORE.md:16-18 and engine.md:67-74 already name and place
   it. It must live as a cross-cutting transform in the `_wire`/invoke path the
   engine owns (the same seam Spec 001 already threads `ToolResult.archived_to`
   through — `001:257,305-310`), **not** as a capability the model invokes by hand.
   It should fire automatically, like quality-score and loop-detection, and write
   the trimmed body's pointer onto the envelope (`archived_to` already exists for
   exactly this — `001` reserves it for the >4 KB trim).

2. **The read-back path = a thin `transform` facet, folded into Memory.** Querying
   "what left the window / what's in the doc corpus" is a read-projection over a
   store. The canon's home for read-projections is **Memory** (`recall · find ·
   project`, CORE.md:38-45) and the `transmute`/`navigate` facets
   (CAPABILITY-CLUSTERS.md:20,23). It does **not** warrant a new concept; at most it
   is one or two `transform` verbs *on the existing `memory`/`reflect` surface*, or
   an engine read-projection alongside `memory_graph_provenance`
   (`engine.py:124-127`).

### Reasoning

- **The canon already drew this line and named this exact mechanism.** "Compaction"
  appears verbatim in BOTH guard lists (CORE.md:17, engine.md:73). A spec cannot
  re-classify a thing the canon has already classified without superseding the
  canon — and CLAUDE.md is explicit: *"The canon wins; code serves it."* Promoting
  compaction to a concept is the precise bloat CORE.md "Dropped (and why)" and
  CAPABILITY-CLUSTERS.md:26-33 were written to prevent.
- **Middleware fires automatically; a capability must be discovered and called.**
  The whole point of compaction-as-guard is that the model does *not* spend tokens
  orienting to it — it just happens in the seam. Making capture a capability means
  the model must `search → get_schema → execute` to reach its own context hygiene,
  which is self-defeating and re-introduces the orienting round-trip the spec
  claims to remove.
- **The triad partially duplicates two existing surfaces.** `context.search /
  describe / read` shadows (a) the engine's own **`search` / `get_schema` /
  `execute`** contract — the canon's ONE lean surface (CORE.md:10-14) — risking a
  "fourth surface," exactly the spec's own stated fear; and (b) Memory's **`recall`
  / `find` / `project`** read-frame (CORE.md:40-45) and `reflect`'s already-shipped
  `search`/`recall` verbs (`reflect.py:34-48`, also `home="memory"`). A
  budget-aware ranked read over a store is what `Memory.project(query, budget)` *is*
  (`memory.py:155`, CORE.md:41-43). The spec even sets `home="memory"` — conceding
  its gravity is Memory, then building a separate concept anyway.
- **What stays valid as a transform facet.** The *funnel* (narrow→narrow→pay:
  ids→previews→one body) is a sound `transform` shape and worth keeping — but as a
  facet of Memory's read surface, surfaced as `transform` verbs, not as a concept
  with its own ontology home. This is the `transmute` cluster
  (CAPABILITY-CLUSTERS.md:20), which the canon explicitly says is *"the open
  `transform` set,"* a facet.

### Why not "full first-class capability" (the spec's current framing)

Because it forces a new concept where the canon has a guard slot and a read-frame
already. It multiplies the public surface (a 4th triad), invites the naming
collision the spec itself flags as unresolved (Open Q-3), and inverts
mechanism/concept. The ~0.9-confidence claim that *"the four concepts + the engine
absorb the entire surface"* (CAPABILITY-CLUSTERS.md:37-43) is a falsification bar
this spec must clear — and it does not: nothing here is un-absorbable by
`engine guard` + `Memory.project` + a `transform` facet.

## Misalignments (ranked)

1. **[CRITICAL] Concept inflation.** `ContextCapability` promotes compaction (a
   named guard, CORE.md:17) to a first-class concept. Inverts CORE.md:16-18.
2. **[CRITICAL] Out-of-scope hook layer.** `hooks/hooks.json` + `ctx_route.py` +
   `ctx_session.py` (PostToolUse / SessionStart / UserPromptSubmit / PreToolUse)
   contradict `Plan/000-overview.md:96-98` ("no hook layer is built yet"; "hook
   layer → out of scope for v1"). The spec adopts a 4-hook slice while claiming a
   narrow one; UserPromptSubmit "capture user decisions" is a *new* concern (it
   manufactures `kind="decision"` state) well beyond capture/attach.
3. **[MAJOR] Surface duplication / 4th-surface risk.** The `search/describe/read`
   triad overlaps the engine's `search/get_schema/execute` (CORE.md:10-14) and
   Memory's `recall/find/project` + `reflect.search` (CORE.md:40-45,
   `reflect.py:43-48`). The spec asks "does this become a 4th surface?" — under the
   capability framing, yes.
4. **[MAJOR] Capture-as-callable defeats its own token goal.** Making context
   hygiene an invokable verb re-imposes orient cost; compaction must be a silent
   seam transform, not a tool the model reaches for.
5. **[MAJOR] Bi-temporal/provenance bypass.** A side SQLite+FTS5 SessionDB stores
   "what left the window" *outside* the one bi-temporal append-only graph that is
   "the moat" (CORE.md:38-45). Trimmed outputs are artefacts; they belong as nodes
   edged into provenance (`PRODUCES`/`SERVES`), reachable by one traversal — not in
   a parallel store with its own multi-writer ADR. This is a second source of truth
   for memory, which the canon's whole thesis argues against.
6. **[MODERATE] Hard ride on 001 Q-2 is correctly flagged but compounds risk.** The
   `next_suggested_tools` glue presumes 001 surfaces the envelope at `_wire`
   (001 Q-2, the plan's one true blocker, `000-overview.md:71-81`). Honest, but it
   means 005's headline mechanism is doubly speculative.
7. **[MINOR] Naming collision unresolved (Open Q-3).** "context-mode" already means
   schema-side progressive disclosure (`CORE.md:11-13`, `docs/guide/usage.md`).
   Reusing it for a concept worsens the ambiguity; as middleware + a facet it can
   simply be "compaction (output-side)" and avoid the collision entirely.

## Recommended aligned framing

Reframe Spec 005 from *"a new ContextCapability + a hook layer"* to *"an engine
compaction guard + a Memory read-projection facet"*:

- **A. Output-overflow compaction as an engine guard (middleware).** Implement the
  summarize-on-overflow transform in the seam the engine already owns
  (`Engine._wire` / `Registry.invoke`), gated by a measured threshold, writing the
  pointer onto the **existing** `ToolResult.archived_to` (Spec 001 reserved it for
  exactly this). It fires automatically; the model never calls it. This is the
  canon's "compaction checkpoint … full record stays in Memory" (engine.md:73)
  realized literally.
- **B. Store the trimmed body in Memory, not a side DB.** The full body becomes a
  node in the one graph (an `Artefact`-like node, `ARCHIVED_FROM` the Invocation),
  so "what left the window" is one provenance traversal and survives `as_of`. If an
  FTS index is needed for ranking, it indexes Memory nodes (an engine detail), not a
  parallel SessionDB with its own writer contract.
- **C. Read-back as a `transform` facet of Memory, not a new triad.** Expose
  retrieval as one or two `transform` verbs on the `memory`/`reflect` surface (or as
  `Memory.project(query, budget)` extended to span doc-corpus + archived outputs).
  Keep the narrow→narrow→pay funnel as the verb's *internal* behavior, returning
  budgeted deltas — that is `project`'s contract already (CORE.md:41-43). No new
  concept, no `home="memory"` capability that competes with Memory itself.
- **D. Fold the doc-corpus discovery (Leak 2) into the same read-projection.** The
  3 hardcoded `develop.reference` strings (`develop.py:86-111,139-145`) and `docs/**`
  become searchable Memory nodes via the manifest, reachable by the same `transform`
  verb. This part is clean and canon-aligned — keep it; just don't hang it off a new
  concept.
- **E. Drop the hook layer from this spec.** Per `000-overview.md:96-98`. The
  PostToolUse capture belongs in the engine seam (A), which needs no Claude-Code
  hook. SessionStart-attach, UserPromptSubmit-decisions, PreToolUse-routing, and the
  whole snapshot/restore pair go to the deferred follow-up (correctly already
  deferred for `PreCompact`; extend that deferral to the rest).
- **F. Keep the measured-trace discipline and the deferrals.** The "no unbacked
  97%/98%", the dropped event taxonomy, the deferred checkpoint/restore — all
  canon-honest. Retain them verbatim.

## Must-change list (blocking before this spec can land)

1. **Demote `ContextCapability` to engine middleware + a transform facet.** Remove
   the new first-class capability/concept. Implement output-overflow capture as a
   cross-cutting guard in `Engine._wire`/`Registry.invoke`, writing
   `ToolResult.archived_to`; expose read-back as `transform` verb(s) on the existing
   `memory`/`reflect` surface (or as an extended `Memory.project`). Cite CORE.md:16-18
   and engine.md:67-74 in the spec's Why as the governing canon. *(Resolves
   misalignments 1, 3, 4.)*
2. **Remove the hook layer (`hooks/hooks.json`, `ctx_route.py`, `ctx_session.py`,
   the `plugin.json` hook registration) from scope.** Per `Plan/000-overview.md:96-98`.
   Output capture lives in the engine seam, not a Claude-Code hook. Defer
   SessionStart/UserPromptSubmit/PreToolUse and all snapshot/restore to the named
   follow-up. *(Resolves misalignment 2.)*
3. **Store trimmed bodies and the doc corpus IN the bi-temporal graph, not a side
   SessionDB.** Make "what left the window" provenance nodes edged to their
   Invocation (one traversal, `as_of`-aware), eliminating the parallel store + its
   multi-writer ADR. Any FTS index is an engine implementation detail over Memory
   nodes. *(Resolves misalignment 5; also dissolves the multi-writer race entirely.)*

### Lower-priority (should-change, non-blocking)

4. Rename to "output-side compaction"; retire "context-mode" as a concept name to
   kill the Open Q-3 collision (CORE.md:11-13). *(Misalignment 7.)*
5. Keep the explicit `depends_on: [001]` and the 001-Q-2 precondition; with the
   `archived_to` reframing (must-change 1), the dependency narrows to a field that
   001 *already reserves*, de-risking the glue. *(Misalignment 6.)*
6. Retain the measured-trace gate, the dropped event taxonomy, and the deferred
   checkpoint/restore as-is — these are canon-faithful and should survive the
   reframe untouched.
