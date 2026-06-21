# Cross-Cluster Idioms — Novel Capability

> Iteration 4 (2026-06-07). The 7 clusters compose through a small,
> well-defined set of idioms. This document is the single source of
> truth for "when does cluster X call cluster Y?" so implementers don't
> re-derive the pattern.

## Idiom 1: `ctx.call(cap, verb, **kw)` — sibling verb invocation

The agency idiom for one verb to invoke another. Per `capability.py:138`,
returns the spawned verb's **unwrapped result dict** (NOT `ToolResult`,
NOT `.data`-wrapped).

```python
result = self.ctx.call("novel", "list_chapters", novel="X")
chapters = result["chapters"]   # direct dict indexing; NO .data
```

**Where used in novel**:
- 103's `novel_coherence_check` calls `103.check_*` per row
- 104's `developmental_gate` calls `104.check_pov_consistency` +
  `104.check_continuity`
- 108's `pre_draft_check` calls `103.novel_coherence_check` +
  `105.verify_gate` + `102.find_novel`
- 107's `publish_package` calls `107.render_manuscript` +
  `107.draft_query_letter` + `107.draft_synopsis`

## Idiom 2: Driver acquisition — `ctx.get_driver(name)`

Cluster verbs that touch external surfaces resolve their Driver lazily:

```python
state = self.ctx.get_driver("music_state")    # reused from music
text  = self.ctx.get_driver("music_text")     # reused
db    = self.ctx.get_driver("music_db")       # reused
cloud = self.ctx.get_driver("music_cloud")    # reused
fmt   = self.ctx.get_driver("novel_format")   # NEW (107)
llm   = self.ctx.get_driver("llm")             # optional (Spec 092 G3)
```

**Why music drivers?** Per 101 driver section: novel REUSES music's
5 drivers verbatim (driver methods are added additively to the same
Boundary). Only FormatDriver is new.

**Failure pattern**: `DriverMissing` raised when driver isn't bound;
verb returns `ToolResult.failure(DEPENDENCY_MISSING, …)` per the
music iteration-5 discipline.

## Idiom 3: Provenance writes — `ctx.record(label, props) + ctx.link`

Every effect verb that creates state records a graph node SERVES the
intent:

```python
node_id = self.ctx.record("ResearchClaim", {
    "text": ..., "verified": "pending",
    "captured_at": int(time.time())})
self.ctx.link(node_id, self.ctx.intent_id, "SERVES")
if novel:
    hits = state.find_novel(novel)
    if hits:
        self.ctx.link(node_id, hits[0]["id"], "RELATES_TO")
```

**Where used in novel**: 102's create_*, 103's storyform writes, 105's
claim recording, 106's beta-feedback inserts, 107's manuscript renders.

## Idiom 4: Gate composition — `ctx.call("gate", "check", ...)`

Composite gate verbs (G1-G8) record a Gate node + flip the lifecycle
state via the core `gate` capability:

```python
self.ctx.call("gate", "check",
              lifecycle_id=lifecycle_id,
              name="pre-draft",
              passed=passed,
              evidence="all green" if passed else f"missing: {missing}")
```

Per music iteration-5 fix: `gate.check` is a core capability verb, NOT
a substrate tool. Reachable via `ctx.call("gate", "check", ...)`.

## Idiom 5: Template rendering — `ctx.template(name)`

Per Spec 060 substrate. Returns a `string.Template`:

```python
album_tpl = self.ctx.template("novel-readme")
body = album_tpl.template   # raw body (mustache placeholders kept; agent fills)
state.put(f"{novel_root}/README.md", {"body": body})
```

**Where used in novel**: 102's `create_novel` renders 5 templates
(novel-readme, work, premise, cast, dramatica); 102's `create_chapter`
renders chapter template; 107's draft-letter/synopsis/blurb renders
those templates.

## Idiom 6: Lifecycle minting (for gates)

The pattern for creating a Lifecycle node that a gate.check can attach to:

```python
# In tests/E2E:
lifecycle_id = eng.memory.record("Lifecycle",
                                 {"state": "working", "phase": 0,
                                  "name": "novel-pipeline"})
eng.memory.link(lifecycle_id, intent_id, "SERVES")
# Now gate.check(lifecycle_id=lifecycle_id, …) works
```

Per the music iteration-5 fix — there is NO `find_lifecycle_for_intent`
helper. Tests mint lifecycles explicitly.

## Idiom 7: Memory.provenance(intent_id) shape

Per music iteration-6 finding — the return shape from
`engine.memory.provenance(intent_id)`:

```python
prov = eng.memory.provenance(intent_id)
prov["serves"]    # list[dict] — every node SERVES the intent
prov["agents"]    # list[dict] — every agent that performed an invocation
prov["artefacts"] # list[dict] — every PRODUCES artefact
prov["gates"]     # list[dict] — every gate.check ledger entry
```

NOT `invocation_count` / `artefact_count` / `node_types` / `edges_from_root`.
Tests filter the lists by label/kind/name.

## Idiom 8: `Memory.link` accepts only declared edge types

```python
# 094 (music) declares music edges.
# 102 (novel) DECLARES every novel-specific edge in its OntologyExtension:
edges={
    "OUTLINES",      # Beat → Scene
    "EMBODIES",      # Character → Throughline-kind via archetype
    "REVISES",       # Draft → Draft
    "ENCODES",       # Scene → Storybeat / Scene → WorldAxiom
    "MANIFESTS",     # Moment → Element
    "BELONGS_TO",    # Character → Faction/House/Family
    "INHABITS",      # Character → Culture
    "WORSHIPS",      # Character → Religion
    "SPEAKS",        # Character → Language
    "WIELDS",        # Character → MagicSystem
    "CONTRADICTS",   # WorldAxiom → WorldAxiom
}
# Reused from music: SERVES, PRODUCES, RELATES_TO, PASSED, BLOCKED_ON.
```

Using an undeclared edge raises at `Memory.link()` time. The novel
capability must declare every edge it intends to use.

## Cluster-by-cluster idiom map

| Cluster | Calls cluster… | For what |
|---|---|---|
| 102 lifecycle | (none — foundation) | — |
| 103 storyform | 102 (StateDriver methods via TextDriver) | Read NCP from `state.read_ncp(novel)` |
| 104 prose | 102 (find_novel, list_chapters) | Resolve novel context for analysis |
| 104 prose | 106 (record EditNote for inline-TODOs) | Persist findings |
| 105 research | `agency.research` (lead/specialist/verify) | The actual heavy lifting |
| 105 research | 102 (find_novel for RELATES_TO linkage) | Link claim → Novel node id |
| 106 catalogue | 102 (read novel/chapter context) | Cross-reference state |
| 107 manuscript | 102 (read full novel state) | Source-of-truth for body |
| 107 manuscript | 104 (read final prose) | Final-pass prose |
| 108 gates | 102, 103, 104, 105, 106, 107 | Composite gate predicates |
| 108 gates | `gate.check` (core) | Lifecycle state writes |
| All effects | `ctx.record` + `ctx.link("SERVES")` | Provenance writes |
