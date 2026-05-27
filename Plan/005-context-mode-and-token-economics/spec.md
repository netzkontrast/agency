---
spec_id: 005
slug: context-mode-and-token-economics
status: draft
owner: "@agency"
depends_on: [001]
affects:
  # NOTE on paths: the Python package is `agency/`. There is NO hook layer and NO
  # `agency/context/` package in this spec — output-side compaction is an ENGINE
  # GUARD in the seam the engine already owns (`_wire`/`Registry.invoke`), and the
  # read-back path is a `transform` facet on the EXISTING memory/`reflect` surface.
  # The vision canon (CORE.md:16-18) names compaction as middleware, not a concept;
  # engine.md:67-74 already owns the "compaction checkpoint" guard slot.
  - agency/engine.py                       # MODIFY — fire output-overflow capture in `_wire`/invoke; write ToolResult.archived_to
  - agency/memory.py                       # MODIFY — archive a trimmed body as a graph node (ARCHIVED_FROM the Invocation); rank read over it
  - agency/capabilities/reflect.py         # MODIFY — add the read-back `transform` verb(s) over archived outputs + the doc corpus
  - agency/capabilities/develop.py         # MODIFY — fold the 3 hardcoded `reference` docs into the searchable corpus
  - agency/ontology.py                     # MODIFY — add the archived-output node kind + `ARCHIVED_FROM` edge to the core ontology
  - tests/test_output_compaction.py        # NEW — guard fires automatically, writes archived_to, body lands in the graph, never breaks invoke
  - tests/test_corpus_readback.py          # NEW — the read-back transform verb finds a doc + an archived output via one Memory traversal
  - docs/vision/specs/engine.md            # MODIFY — pin the compaction-checkpoint guard's mechanism (the slot it already owns)
source-repos:
  - "context-mode @ https://github.com/mksglu/context-mode  # PATTERN-ONLY, read-only; ELv2 — copy NO source, consume NO API"
  - "the-agency-system @ 0a6a9e71f6c26bc120a8fc1db02f8990b7916f22  # exemplar Plan/108 + 111/112/114/120/130 (pattern only)"
estimated_jules_sessions: 2
domain: cross
wave: B
---

# Spec 005 — Output-side Compaction (an engine guard) & Token Economics

> Read `docs/vision/CORE.md` first. **The canon wins; code serves it.** This spec
> does **not** add a new concept. Output-side context economy is an **engine guard
> (middleware)** plus a thin **`transform` facet** on the existing Memory surface —
> exactly where the canon already places it (`CORE.md:16-18`: *"compaction … are
> engine middleware, **not** concepts"*; `docs/vision/specs/engine.md:67-74`: the
> guards table already owns *"compaction checkpoint — named checkpoint that prunes
> working context; full record stays in Memory."*). Build it RED→GREEN; paste
> evidence under `## Evidence`. Only modify paths under `affects:`.

## Why

The engine already pays the **boot** token cost well: `Engine.build_mcp` wraps the
server in FastMCP's `CodeMode()` transform (`agency/engine.py:91-95`), so the only
tools the model sees at start are `search` / `get_schema` / `execute`. That is the
schema-side win the repo's own docs call "context-mode" (`docs/guide/usage.md:36,61`,
`docs/vision/CORE.md:11-13`): progressive *schema* disclosure. **That meaning is
load-bearing and stays.** The in-sandbox half is also already banked —
intermediate `call_tool` results stay in the Monty sandbox, only deltas cross
(`CORE.md:10-14`, `engine.md:50-55`). This spec closes the *remaining* runtime
sinks **without erecting a parallel surface** — it realizes the canon's already-named
compaction guard and a Memory read-projection.

Three token leaks survive the boot + in-sandbox wins — each grounded in this tree:

1. **Bare-dict returns lose the model's place** — `agency/engine.py:73-74`
   (`_wire.impl`) returns `out if isinstance(out, dict) else {"result": out}`: a
   shapeless dict with no `next_suggested_tools`. After an `execute`, the model has
   nothing telling it the next step. **Spec 001 closes this** — its `ToolResult`
   envelope (field **`data`**, plus `next_suggested_tools` and a reserved
   `archived_to`; `Plan/001…/spec.md:90-93,184-216`) is the wire shape this spec
   rides. 005 is its first heavy consumer.
2. **The doc corpus is a single hardcoded verb** — `agency/capabilities/develop.py:139-145`
   (`reference`) serves exactly 3 strings from the in-module `REFERENCES` dict
   (`develop.py:86-111`); everything else in `docs/**` is unreachable through the
   engine. The model can *fetch* one of three known topics but cannot *discover* a
   doc. Discovery is a read-projection — and the canon's home for ranked,
   budget-capped read-projection is **Memory** (`Memory.project(query, budget)`,
   `memory.py:155`, `CORE.md:40-45`).
3. **Large tool outputs cross into context whole** — a `mcp__github__pull_request_read`,
   a filesystem walk, a 50-KB log dump pays its full payload into the window. There
   is no compaction guard trimming an oversize body and leaving a pointer. **The
   canon already names this exact mechanism** — "compaction checkpoint … prunes
   working context; full record stays in Memory" (`engine.md:73`) — as a *guard*,
   and Spec 001 already **reserves `ToolResult.archived_to`** for *"a >4 KB body …
   trimmed"* (`001:290,338-343`). The slot exists; this spec fills it.

### Why a guard + a facet, NOT a `ContextCapability`

An earlier draft of this spec promoted output-capture to a first-class
`ContextCapability` (a `search`/`describe`/`read` triad) plus a Claude-Code hook
layer. The vision review (`VISION-REVIEW.md`) rejected that shape against the canon
on two counts, and this rewrite adopts its ruling verbatim:

- **Compaction is middleware, not a concept** (`CORE.md:16-18`, `engine.md:67-74`).
  A spec cannot re-classify a thing the canon has already classified as a guard
  without superseding the canon. Promoting it would be the precise bloat
  `CAPABILITY-CLUSTERS.md:26-33` was written to prevent.
- **A guard fires automatically; a capability must be discovered and called.** The
  whole point of compaction is the model does *not* spend tokens orienting to its
  own context hygiene — it happens in the seam, like quality-score and
  loop-detection. Making capture a callable verb re-imposes the orienting
  round-trip the spec claims to remove.
- **No fourth surface.** A `search`/`describe`/`read` triad shadows the engine's
  ONE lean `search`/`get_schema`/`execute` contract (`CORE.md:10-14`) *and* Memory's
  `recall`/`find`/`project` read-frame (`CORE.md:40-45`) and `reflect`'s shipped
  `search`/`recall` (`reflect.py:42-48`, also `home="memory"`). A budget-aware
  ranked read over a store **is** `Memory.project(query, budget)`. The read-back
  belongs as a `transform` facet on that surface, not a new triad.
- **One source of truth for memory.** A side SQLite/FTS5 SessionDB stores "what
  left the window" *outside* the one bi-temporal graph that is "the moat"
  (`CORE.md:38-45`). Trimmed outputs are artefacts; they belong as nodes edged into
  provenance (`ARCHIVED_FROM` the Invocation, `as_of`-aware), reachable by one
  traversal — not in a parallel store with its own multi-writer ADR. Storing them
  in the graph also **dissolves the multi-writer race entirely** (one writer: the
  engine).

So this spec ships **(A) an engine compaction guard** + **(B) the trimmed body as a
graph node** + **(C) a `transform` read-back facet on the existing Memory/`reflect`
surface** + **(D) the doc corpus folded into that same read-projection**. No new
concept, no `agency/context/` package, no hook layer.

### No hook layer (Plan/000 forbids it for v1)

`Plan/000-overview.md:96-98` resolved: *"Hook layer → **out of scope for v1** …
context-mode snapshot/restore is deferred (Plan-120 territory); **no hook layer is
built yet.**"* Output capture needs no Claude-Code hook — it lives in the engine
seam the engine already owns (`_wire`/`Registry.invoke`). The `SessionStart`-attach,
`UserPromptSubmit`-decisions, `PreToolUse`-routing handlers, and the whole
`PreCompact`→`SessionStart` snapshot/restore pair are deferred to the named
follow-up (Plan/120 `smart-compaction-checkpoints` depth: `pick_richest`, decision
regex, ≤2 KB checkpoint) — adopted honestly later rather than half-built here.

Schema-side context-mode (boot) + in-sandbox deltas (existing) + this output-side
compaction guard (new) bracket the token sinks; the `ToolResult` envelope (Spec 001)
stitches them into a guided loop via `next_suggested_tools` and `archived_to`.

## Done When

- [ ] **Output-overflow capture is an engine guard that fires automatically** in the
      invoke/`_wire` seam (`agency/engine.py:69-74` / `Registry.invoke`), NOT a
      capability the model calls. When a verb's `ToolResult.data` body exceeds a
      measured threshold (see `## Design` → threshold), the guard: (a) archives the
      full body into Memory as a node, (b) replaces the in-context body with a
      token-tiny summary, and (c) sets **`ToolResult.archived_to`** to the archive
      node's id (the field Spec 001 already reserves for *"a >4 KB body … trimmed",*
      `001:290,338-343`). Small bodies pass through unchanged. The guard NEVER
      raises into the caller — on any internal failure it passes the body through
      untrimmed (a guard must never break invoke).
- [ ] **The trimmed body lives in the one bi-temporal graph, not a side store.**
      `agency/memory.py` gains an archive write: `record("ArchivedOutput",
      {kind, title, body, bytes})` + `link(archive_id, invocation_id,
      "ARCHIVED_FROM")`, so "what left the window" is one provenance traversal and
      survives `as_of`. `agency/ontology.py` adds the `ArchivedOutput` node kind and
      the `ARCHIVED_FROM` edge to the **core** ontology (merged + enforced like every
      node). No SQLite SessionDB, no FTS5 SessionDB, no WAL/`busy_timeout`
      multi-writer contract — there is one writer (the engine).
- [ ] **Read-back is a `transform` verb on the EXISTING Memory/`reflect` surface**,
      not a new triad and not a new `home="memory"` capability that competes with
      Memory. Add `reflect.project(query, budget=…, kind=None)` (role `transform`)
      that ranks the merged corpus — archived outputs (`kind="tool-output"`) + the
      static doc corpus (`kind="doc"` / `kind="discipline-howto"`) — by relevance,
      returns budgeted deltas through the Spec 001 envelope, and sets
      `next_suggested_tools` to the actionable capability for the top hit's `kind`.
      It reuses Memory's existing `find`/`project` machinery (`memory.py:128-159`);
      the narrow→narrow→pay funnel (ids/snippets → one full body) is the verb's
      *internal* behavior (a `view` arg: `summary` vs `full`), NOT three separate
      public verbs. (Naming: `project` is the canon's read-projection verb,
      `CORE.md:41`; if a distinct verb name is preferred it MUST stay a `reflect`
      `transform` facet, never a new concept — see Open Questions.)
- [ ] Every touched verb and the guard return through the Spec 001 `ToolResult`
      envelope **exactly as 001 defines it** — fields `ok`, `data`, `warnings`,
      `artefacts_written`, `next_suggested_tools`, `error`, `archived_to`
      (`Plan/001…/spec.md:184-216,310-343`); the payload lives under **`data`**, NOT
      a legacy `result` key (`result` is what `_wire` strips today at
      `engine.py:73`; `reflect.py:32,40,48` and `develop.py:124,144-145` still emit
      `{"result": …}` and migrate as 001 lands).
- [ ] `agency/capabilities/develop.py:139-145` (`reference`) no longer hardcodes the
      doc body as the only path: the 3 `REFERENCES` strings are registered into the
      searchable corpus as `kind="discipline-howto"` Memory nodes (via the manifest
      step below), so `reflect.project("best-practices")` *discovers* them. The 3
      docs remain reachable (`reference` may thin-delegate to the read-back verb or
      stay as a direct fetch); a test proves discovery finds `best-practices`.
- [ ] **A manifest step loads the static doc corpus** (`docs/**` + the 3 develop
      references) into the SAME graph as `kind="doc"` / `kind="discipline-howto"`
      nodes so the read-back facet searches one merged corpus. Rebuild is
      **mtime/sha256-gated** (matching the exemplar Plan/111 drift guard); the
      trigger is a lazy first-`project` rebuild (this spec ships **no**
      `SessionStart` hook to trigger it — see "No hook layer").
- [ ] **Measured token before/after** (see `## Design` → Token economics): a real
      trace of "find and read the `best-practices` doc" AND a re-read of a large
      output through the guard are captured with a token counter (not asserted from
      memory); the before/after numbers are pasted under `## Evidence`; the savings
      claim matches the trace (no bare "97%"/"98%" without the trace). The chosen
      capture threshold is justified by that same trace.
- [ ] `tests/test_output_compaction.py` + `tests/test_corpus_readback.py` pass;
      `pytest -q` stays green (was 56 passing). Tests cover:
      (a) the guard trims an over-threshold body, writes `archived_to`, and the body
      is retrievable from the graph; (b) a small body passes through untrimmed;
      (c) the guard NEVER raises into invoke — an archive failure passes the body
      through and returns `ok=True`; (d) `reflect.project` finds a `kind="doc"` and a
      `kind="tool-output"` node via ONE Memory traversal and returns budgeted deltas;
      (e) `reflect.project("best-practices")` discovers the migrated develop ref;
      (f) read-back degrades gracefully (`ok=True`, empty matches) when the corpus is
      empty, and returns `ToolResult.failure(BOUNDARY_ERROR, …)` (Spec 001 `Codes`,
      `001:184-188`) — never an unhandled raise — when the graph read errors.
- [ ] No source from the external `context-mode` plugin is copied into the tree and
      no `context-mode` API is consumed (Plan/000 resolved: **reimplement in-tree**;
      ELv2 makes a runtime dep toxic for an opt-in plugin). The pattern (oversize-body
      trim + a ranked read over a store) is reimplemented on the engine's own
      primitives — the one graph and `Memory.project`.

## Design

### How it composes with code-mode and the ToolResult envelope (Spec 001)

Three orthogonal token axes, one loop — none a new concept:

| Axis | Owns | Mechanism | Where |
|---|---|---|---|
| **schema-side context-mode** (existing) | tool *schemas* | `CodeMode()` + `search`/`get_schema`/`execute` | `engine.py:91-95` |
| **in-sandbox deltas** (existing) | intermediate *results* | Monty sandbox; only deltas cross | `engine.md:50-55`, `CORE.md:10-14` |
| **output-side compaction** (this spec) | oversize tool *outputs* | an **engine guard** in `_wire`/invoke → trims body, archives to the graph, writes `ToolResult.archived_to`; a **`transform` read-back facet** on Memory/`reflect` | `engine.py:_wire`, `memory.py`, `reflect.project` |
| **ToolResult envelope** (Spec 001) | the *seam between steps* | `ok` + **`data`** + `warnings` + `artefacts_written` + `next_suggested_tools` + `error` + **`archived_to`** | `engine.py:_wire`, all verbs |

> **The canon already drew this line.** "Compaction" appears verbatim in BOTH guard
> lists (`CORE.md:17`, `engine.md:73`). This spec realizes that guard literally —
> "prunes working context; full record stays in Memory" — and adds a read-projection
> facet so the model can pull the pruned body back when it needs the slice. It
> invents no wire shape: Spec 001's `ToolResult` **is** the wire shape, and
> `archived_to` is the field 001 already reserves for exactly this trim.

### (A) The output-overflow compaction guard (middleware)

The guard lives in the seam every verb already passes through —
`Registry.invoke` → `Engine._wire.impl` (`engine.py:69-74`). It runs AFTER the verb
returns its `ToolResult` and BEFORE the envelope serialises to the model:

```
result = reg.invoke(...)                      # the verb's ToolResult
if byte_len(result.data) > THRESHOLD:         # measured threshold (see below)
    archive_id = memory.record("ArchivedOutput",
                   {"kind": "tool-output", "title": <verb>, "body": <full data>,
                    "bytes": byte_len(result.data)})
    memory.link(archive_id, invocation_id, "ARCHIVED_FROM")
    result.data = {"summary": <tiny summary>, "bytes": <n>}
    result.archived_to = archive_id           # the field Spec 001 reserves (001:290)
return result.to_dict()                        # the model sees a summary + a pointer
```

- It **fires automatically** — the model never calls it; it is a cross-cutting
  guard exactly like quality-score and loop-detection (`engine.md:67-74`). This is
  the property that makes it free: no orienting round-trip to reach context hygiene.
- It **never breaks invoke** (Nygard): the trim is wrapped so any archive/record
  failure falls back to passing `result.data` through untrimmed and returning
  `ok=True`. A guard that can break a tool call is worse than no guard.
- It writes the body to the **one graph** (B), so the pointer in `archived_to`
  resolves by a normal Memory read — no second store, no egress.

### (B) The trimmed body is a graph node (no side store)

`agency/ontology.py` adds to the **core** ontology:
- node `ArchivedOutput` with required fields `kind`, `title`, `body`, `bytes`;
- edge `ARCHIVED_FROM` (an `ArchivedOutput` → the `Invocation` that produced it).

`agency/memory.py` writes it through the existing `record`/`link` (ontology-enforced)
and reads it through the existing `find`/`recall`/`project` (`memory.py:70-82,
118-159`). "What left the window this intent" is then a single provenance traversal —
the moat the side-DB design forfeited. Because there is exactly one writer (the
engine, single logical thread, `memory.py:26-37`), **the multi-writer race the old
SessionDB design needed an ADR for simply does not exist.** If ranking ever needs an
FTS index, it is an engine implementation detail over Memory nodes (a SQLite FTS5
table the engine owns alongside the graph), NOT a parallel canon — and out of scope
until the measured trace proves substring ranking insufficient.

### (C) Read-back as a `transform` facet on Memory/`reflect`

Retrieval is one `transform` verb on the **existing** `reflect` capability
(`home="memory"`, `reflect.py:17-23`) — it does NOT get its own concept, ontology
home, or `search`/`describe`/`read` triad:

```
reflect.project(query, budget=20, kind=None, view="summary")
  -> ToolResult.success(
       data={matches:[{id, kind, title, score, snippet}], next_cursor},
       next_suggested_tools=<actionable cap for the top hit's kind>)

reflect.project(query, view="full", id=<one id>)
  -> ToolResult.success(data={id, kind, body},
       next_suggested_tools=<actionable cap for that kind>)
```

- `kind` partitions the merged corpus: `doc` (static `docs/**`), `discipline-howto`
  (the migrated develop references), `tool-output` (archived live payloads from the
  guard).
- The **narrow→narrow→pay funnel is internal** to the verb (`view="summary"` returns
  ids + snippets; `view="full"` pays a body for ONE id), mirroring Plan/112's view
  ladder and the FastMCP code-mode loop — but as one `project` verb's behavior, not
  three public verbs. This keeps the surface lean (`CORE.md:10-14`) and reuses
  `Memory.project`'s budgeted-delta contract (`CORE.md:41-43`, `memory.py:155-159`).
- `next_suggested_tools` is the glue (Spec 001's field, `001:184-216`): a
  `discipline-howto` hit points at `capability_develop_checklist`; a `tool-output`
  hit points at the capability that produced it. **This presumes 001 Open Q-2
  resolves in favour of surfacing the envelope at `_wire`** — see Open Questions. The
  reframe NARROWS that dependency: `archived_to` is a field 001 *already reserves*,
  so the guard's half (A) needs only the field, not the full glue.

> **Why no event taxonomy.** The exemplar's Plan/108 carried a ~23/26-category
> `event_map.py` *because* it bridged outputs into a Spec 100 SessionLog event stream
> (live context-mode lists 23 categories). Agency has no SessionLog to map into, so
> this spec deliberately uses just three `kind`s and ships no event taxonomy.

### (D) Fold the doc corpus into the same read-projection

A manifest step loads `docs/**` + the 3 `develop.REFERENCES` strings into the graph
as `kind="doc"` / `kind="discipline-howto"` `ArchivedOutput`-family nodes, so the one
`reflect.project` verb reaches BOTH the static corpus AND the live archived outputs.
This is the clean, canon-aligned half of the original spec — kept, just not hung off
a new concept. Rebuild is mtime/sha256-gated (Plan/111 drift guard) and triggered
lazily on first `project` (no `SessionStart` hook — see "No hook layer").

### Token economics — the measured trace

Task A: *find and read the `best-practices` development doc, then act on it.*
Task B: *re-encounter a 50-KB log dump already seen this session.*

**Before** (today's tree, code-mode boot + in-sandbox already applied):
- `develop.reference(topic="best-practices")` returns the full ~500-token body
  (`develop.py:103-110`) — and the model had to *already know* the topic string;
  no discovery path exists.
- The bare-dict return (`engine.py:73-74`) carries no `next_suggested_tools`, so the
  model spends an orienting round-trip (~300 tokens) to find the next capability.
- The 50-KB dump (~12k tokens) crosses into context whole, every time.

**After** (this spec + Spec 001 envelope):
- `reflect.project("best-practices")` → ~50-token id list, `next` → read the body.
- `reflect.project(view="full", id="best-practices")` → ~500-token body, `next` →
  the actionable capability (no orienting round-trip; the envelope named it).
- The 50-KB dump hits the **guard**: a ~150-token summary + an `archived_to`
  pointer cross; the body stays in the graph; the model `reflect.project`s only the
  slice it needs.

**Every numeric figure above is an UNMEASURED placeholder.** The Done-When gate
requires a real counted trace (a tokenizer over the actual `ToolResult` JSON for each
step) before any number — or any percentage — is asserted in prose. Assert the
*method*, not the percentage; do not ship "97%/98%" unbacked.

### The capture threshold (needs a measured value)

The guard threshold is **not asserted**. Prior art disagrees: Spec 001 reserves
`archived_to` for *">4 KB"* (`001:290,338-343`); the live context-mode repo routes at
**5 KB**; Plan/108 cited context-mode's ">2 KB" rule; Plan/114's read-cache uses
50 KB / 2,000-line / 1,000-token minimums. The guard ships a configurable default;
the chosen value is justified by the same measured trace that backs the token
numbers — aligning with Spec 001's reserved >4 KB intercept by default, not picked
from memory.

## Files

> **Path discipline (verified against the tree).** The Python **package** is
> `agency/` (import target). This spec touches ONLY the package + tests + one
> vision doc — there is **no** hook layer (`hooks/`, `agency/hooks/`), **no**
> `agency/context/` package, **no** `skills/ctx-insight` or `commands/ctx-insight`,
> and **no** `.claude-plugin/plugin.json` change. Those were the parallel-surface /
> hook-layer artefacts the vision review removed.

- **Create**:
  - `tests/test_output_compaction.py` — the guard fires automatically over the
    threshold, writes `archived_to`, archives the body to the graph, never raises
    into invoke; small bodies pass through.
  - `tests/test_corpus_readback.py` — `reflect.project` finds a `doc` and a
    `tool-output` node via one Memory traversal; discovers the migrated
    `best-practices` ref; degrades gracefully on empty/error.
- **Modify**:
  - `agency/engine.py` — add the output-overflow guard in the invoke/`_wire` seam
    (`engine.py:69-74`): trim oversize `ToolResult.data`, archive to Memory, set
    `archived_to`. Fires automatically; never raises into the caller.
  - `agency/memory.py` — archive-write helper (`record("ArchivedOutput", …)` +
    `link(..., "ARCHIVED_FROM")`) and the ranked read the facet uses (reuse
    `find`/`project`, `memory.py:128-159`).
  - `agency/ontology.py` — add the `ArchivedOutput` node + `ARCHIVED_FROM` edge to
    the core ontology (enforced like every node).
  - `agency/capabilities/reflect.py` — add the `project` read-back `transform` verb
    (merged corpus, budgeted deltas, `view` funnel, `next_suggested_tools`).
  - `agency/capabilities/develop.py` — register the 3 `REFERENCES` bodies into the
    searchable corpus (`develop.py:86-111,139-145`); keep them reachable.
  - `docs/vision/specs/engine.md` — pin the compaction-checkpoint guard's mechanism
    in the guards table (`engine.md:67-74`): the slot this spec fills.
- **Move / Delete**: none.

## Open Questions / Needs Research

0. **[CRITICAL-PATH BLOCKER, NARROWED by the reframe] Spec 001 Open Q-2 — does the
   envelope surface at `_wire`?** The read-back facet's `next_suggested_tools` glue
   presumes the `ToolResult` envelope (or at least `next_suggested_tools`) reaches
   the model at the `execute()`/`_wire` boundary. **Spec 001 has not yet decided
   this** (`Plan/001…/spec.md:359-366`; `Plan/000-overview.md:71-81` lists it as the
   one true cross-cutting blocker). **The reframe narrows the exposure:** part (A),
   the guard, needs only `ToolResult.archived_to` — a field 001 *already reserves*
   (`001:290`) — so output capture lands even if Q-2 keeps the unwrapped-`data`
   contract; only the (C) read-back glue depends on Q-2. Precondition: the
   `next_suggested_tools` portion cannot fully land until 001 Q-2 resolves in favour
   of surfacing the envelope. Hard dependency on `depends_on: [001]`.
1. **Read-back verb name — `reflect.project` vs a dedicated facet name.** The canon's
   read-projection verb is `project` (`CORE.md:41`, `memory.py:155`). Adding it to
   `reflect` (already `home="memory"`, with `search`/`recall`, `reflect.py:17-48`)
   keeps it a facet. Open: whether to (a) extend `Memory.project` directly,
   (b) add `reflect.project`, or (c) generalize `reflect.search` to span the corpus.
   ANY choice MUST stay a `transform` facet on the existing memory surface — never a
   new concept or a `search`/`describe`/`read` triad. Resolve before code.
2. **Ranking method — substring vs FTS index.** `reflect.search` today is
   deterministic substring (`reflect.py:42-48`); `Memory.project` is recency-ranked
   (`memory.py:155-159`). Open whether the merged-corpus read needs a real relevance
   rank (an engine-owned SQLite FTS5 index over Memory nodes — an *implementation
   detail*, NOT a parallel canon) or substring suffices. Decide by the measured
   trace; default to substring until proven insufficient.
3. **Capture threshold value — hard gate (a Done-When item).** The guard threshold is
   an UNMEASURED placeholder. Needs a counted run before the doc pins a value. Prior
   art disagrees (Spec 001 ">4 KB"; context-mode 5 KB; Plan/108 ">2 KB"; Plan/114
   50 KB). Default to 001's reserved >4 KB; cite the chosen value, do not assert it.
4. **Summary generation — deterministic vs sampled.** The guard's tiny summary can be
   a deterministic head/tail+shape truncation (cheap, no LLM call in the seam) or an
   `ctx.sample` call. Default to deterministic truncation in the guard (a guard
   should not block on an LLM round-trip); a richer summary is a follow-up. Confirm.
5. **Manifest staleness — mtime/sha256-gated, lazy first-`project` trigger.** Matching
   Plan/111's drift guard. Because there is **no `SessionStart` hook** in this spec,
   the rebuild triggers lazily on first read-back. Confirm the lazy trigger is
   acceptable vs an explicit `reflect`-verb rebuild.

### Deferred (canon-honest, kept from the prior draft)

6. **Snapshot/restore (`PreCompact`→`SessionStart`) — deferred.** The checkpoint
   pattern (Plan/120: `pick_richest`, decision regex, ≤2 KB checkpoint,
   `compose_digest`) and the whole hook layer are out of scope per
   `Plan/000-overview.md:96-98`. A follow-up adopts Plan/120's depth honestly rather
   than half-implementing it here.
7. **PreToolUse read-cache (deferred).** Plan/114 (`read-cache-delta-mode`) proposes a
   `difflib.unified_diff` read-cache for repeated file reads — a standalone follow-up,
   a separate concern from output compaction.
8. **`UserPromptSubmit` decision capture (deferred).** Manufacturing `kind="decision"`
   state from user prompts is a *new* concern beyond compaction; it needs the hook
   layer (out of scope) and belongs with the Plan/120 snapshot follow-up.

## Evidence

- Canon ruling — compaction is middleware, not a concept: `docs/vision/CORE.md:16-18`
  (*"Cross-cutting guards (quality-score, loop-detection, **compaction**, `Slot`/quota)
  are engine **middleware, not concepts.**"*). The guard slot already exists:
  `docs/vision/specs/engine.md:67-74` (*"compaction checkpoint — named checkpoint that
  prunes working context; full record stays in Memory."*).
- No new primitives sanctioned: `CAPABILITY-CLUSTERS.md:26-33` (only `delegate` +
  `research` were net-new; context-mode is not on that list). `transmute` (*"views,
  indexes, summaries, tool-list shaping"*) is the open `transform` set — a facet
  (`CAPABILITY-CLUSTERS.md:20`).
- No hook layer in v1: `Plan/000-overview.md:96-98` (*"Hook layer → out of scope for
  v1 … no hook layer is built yet."*).
- Boot win already banked: `agency/engine.py:91-95` (`CodeMode()` transform);
  in-sandbox deltas: `docs/vision/specs/engine.md:50-55`, `docs/vision/CORE.md:10-14`.
- Leak 1 (bare dicts, no `next_suggested_tools`): `agency/engine.py:73-74`.
- Leak 2 (single hardcoded doc loader): `agency/capabilities/develop.py:139-145`
  (`reference`) over `develop.py:86-111` (the 3-entry `REFERENCES` dict).
- Leak 3 (no compaction guard on outputs): the invoke/`_wire` seam at
  `agency/engine.py:69-74` returns the body whole; no trim.
- Spec 001 envelope field is **`data`**, with `archived_to` RESERVED for the >4 KB
  trim this spec fills: `Plan/001-toolresult-and-typed-errors/spec.md:90-93`
  (`ToolResult.data`), `:184-216,310-343` (`to_dict()` emits `{ok, data, warnings,
  artefacts_written, next_suggested_tools, error, archived_to}`), `:290,338-343`
  (`archived_to` = *"a >4 KB body … trimmed"*). The legacy `result` key is what
  `_wire` strips today (`engine.py:73`; `reflect.py:32,40,48`, `develop.py:124,
  144-145` still emit `{"result": …}`).
- 001's critical-path Open Q-2 (envelope surfacing at `_wire`):
  `Plan/001…/spec.md:359-366`; `Plan/000-overview.md:71-81`.
- Memory is the canon home for ranked, budget-capped read-projection:
  `docs/vision/CORE.md:38-45`, `agency/memory.py:155-159` (`project(label, budget,
  as_of)`); `reflect` is already `home="memory"` with `search`/`recall`:
  `agency/capabilities/reflect.py:17-48`.
- One bi-temporal graph is the moat (one traversal, `as_of`): `docs/vision/CORE.md:38-45`,
  `agency/memory.py:118-220`; the ontology is enforced on `record`/`link`:
  `agency/memory.py:70-82`, `agency/ontology.py`.
- ELv2 / reimplement-in-tree resolved: `Plan/000-overview.md:90-92`
  (*"`context-mode` is reimplemented in-tree (ELv2 makes a runtime dep toxic)"*).
- Pattern-only prior art (no source copied): the-agency-system Plan/108 (capture
  pattern), Plan/111 (mtime/sha256 drift guard), Plan/112 (view ladder), Plan/120
  (deferred checkpoint depth); live context-mode (23 event categories, 5 KB threshold,
  ELv2) — patterns only.
