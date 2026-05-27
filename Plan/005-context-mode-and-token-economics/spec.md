---
spec_id: 005
slug: context-mode-and-token-economics
status: draft
owner: "@agency"
depends_on: [001]
affects:
  # NOTE on paths: the Python package is `agency/`, BUT the plugin metadata,
  # `skills/`, and `commands/` live at the REPO ROOT (verified:
  # `.claude-plugin/plugin.json`, `skills/brainstorming`, `commands/help.md`).
  # Hooks ship as root-level config too; their handler scripts live under the
  # importable `agency/` package so the engine and the hook subprocess share code.
  - agency/capabilities/context.py        # NEW — the search/describe/read triad
  - agency/capabilities/develop.py         # MODIFY — fold `reference` into context, or delegate to it
  - agency/engine.py                       # MODIFY — context cap auto-wires like any other; inject the shared Index
  - agency/context/__init__.py             # NEW — output-side index package re-exports
  - agency/context/index.py                # NEW — SessionDB (SQLite + FTS5) over large tool OUTPUTS
  - agency/context/summarize.py            # NEW — output -> summary + stored handle
  - agency/context/manifest.py             # NEW — build/load the doc corpus manifest the triad searches
  - hooks/hooks.json                       # NEW (ROOT) — the Claude-Code hook entry points
  - agency/hooks/ctx_route.py              # NEW — PreToolUse routing + PostToolUse output capture (stdin JSON in, decision JSON out)
  - agency/hooks/ctx_session.py            # NEW — SessionStart (restore) + UserPromptSubmit (capture decisions) handlers
  - skills/ctx-insight/SKILL.md            # NEW (ROOT) — the local /ctx-insight surface (read the SessionDB index)
  - commands/ctx-insight.md                # NEW (ROOT) — the `/ctx-insight` slash command
  - .claude-plugin/plugin.json             # MODIFY (ROOT) — register hooks/ + the new command (additive)
  - tests/test_context_capability.py       # NEW — triad + next_suggested_tools + envelope composition
  - tests/test_context_hooks.py            # NEW — hook contract: route, summarize, round-trip, graceful-offline, locked-DB
  - docs/vision/specs/context-mode-output-side.md  # NEW — disambiguate the two "context-mode"s; lifecycle diagram
source-repos:
  - "context-mode @ https://github.com/mksglu/context-mode  # PATTERN-ONLY, read-only; ELv2 — copy NO source"
  - "FastMCP (fastmcp[code-mode]) — CodeMode transform; https://gofastmcp.com/servers/transforms/code-mode"
  - "the-agency-system @ 0a6a9e71f6c26bc120a8fc1db02f8990b7916f22  # exemplar Plan/108 + 111/112/114/120/130"
estimated_jules_sessions: 3
domain: cross
wave: B
---

# Spec 005 — Context Mode (output-side) & Token Economics

> Read `docs/vision/CORE.md` first. This spec adds a capability **by extension**
> (drop a file in `agency/capabilities/`, it self-registers and auto-wires) plus
> a Claude-Code hook layer that lives OUTSIDE the engine. It does **not** touch
> the core concepts. Build it RED→GREEN; paste evidence under `## Evidence`.
> Only modify paths under `affects:`.

## Why

The engine already pays the **boot** token cost well: `Engine.build_mcp` wraps the
server in FastMCP's `CodeMode()` transform (`agency/engine.py:91-95`), so the only
tools the model sees at start are `search` / `get_schema` / `execute`. That is the
schema-side win — what the repo's own docs already call "context-mode"
(`docs/guide/usage.md:36,61`, `docs/vision/CORE.md:11-13`): progressive *schema*
disclosure. **That meaning is load-bearing and stays.** This spec adds the
*complementary* half — handling tool **outputs** at runtime — and adopts the name
the external [`context-mode`](https://github.com/mksglu/context-mode) plugin uses
for that pattern. The naming clash is real and is resolved explicitly in `## Open
Questions` and in `docs/vision/specs/context-mode-output-side.md`.

Three token leaks survive the boot win — each grounded in this tree:

1. **Bare-dict returns lose the model's place** — `agency/engine.py:74`
   (`_wire.impl`) returns `out if isinstance(out, dict) else {"result": out}`: a
   shapeless dict with no `next_suggested_tools`. After every `execute`, the model
   must re-`search` / re-`get_schema` to find the next step — a full orienting
   round-trip per action. (Spec 001 adds the `ToolResult` envelope — with the
   field named **`data`**, not `result`; see `agency/Plan/001…/spec.md:90-93,
   209-216`. This spec is its first heavy consumer, and depends on 001 resolving
   its Open Q-2 so the envelope actually surfaces at `_wire` — see Open Questions.)
2. **The doc corpus is a single hardcoded verb** — `agency/capabilities/develop.py:140`
   (`reference`) serves exactly 3 strings from the in-module `REFERENCES` dict
   (`develop.py:86-111`); everything else in `docs/` is unreachable through the
   engine. The model cannot *discover* a doc, only fetch one of three known topics.
3. **Large tool outputs cross into context whole** — there is no output-side
   index. A `mcp__github__pull_request_read`, a filesystem walk, a 50-KB log dump,
   or a repeated file Read pays its full payload into the window every time. The
   engine has no `PostToolUse` seam to route those into a searchable store and
   return a summary instead.

The external plugin solves (3) at the **Claude-Code hook layer**. Its verified
hook contract (WebFetched 2026-05-27 from the live repo) is:
`PreToolUse`=enforce sandbox **routing** before a tool runs, `PostToolUse`=capture
the tool's output into the session store, `UserPromptSubmit`=extract **user
decisions/corrections**, `PreCompact`=build a priority-tiered **snapshot** of
session state before compaction, `SessionStart`=**restore** state after a
compaction or resume. The output capture routes large outputs into a local SQLite
**SessionDB** indexed with **FTS5/BM25** and returns only a summary plus a handle,
exposing the stored detail through a local `/ctx-insight` surface.

**This spec adopts only the `PostToolUse`-capture + `SessionStart`-attach slice**
and fuses it with the engine: the hook layer's SessionDB is the same corpus the
new **`ContextCapability`** triad (`search` / `describe` / `read`) searches — so
the model reaches *both* the static doc manifest *and* the live session outputs
through one in-engine triad, while the model's place is held by
`next_suggested_tools` on every return. The **snapshot/restore pair**
(`PreCompact`→`SessionStart` checkpointing) is a separate concern (the exemplar's
Plan/120 `smart-compaction-checkpoints`: richness-weighted `pick_richest`,
decision extraction, an ≤2 KB checkpoint) and is **explicitly deferred** to a
follow-up spec — this spec uses `SessionStart` only to attach the DB, not to
restore a checkpoint, and does **not** ship a `PreCompact` handler.

Schema-side context-mode (boot) + output-side context-mode (runtime) bracket the
two biggest token sinks; the `ToolResult` envelope (Spec 001) stitches them into a
guided loop.

## Done When

- [ ] `agency/capabilities/context.py` defines a `ContextCapability(CapabilityBase)`
      (`name = "context"`, `home = "memory"`) with exactly three verbs. The third
      verb is named **`read`** (not `invoke`) to match the document-side prior-art
      triad `context_search`/`context_describe`/`context_read`
      (the-agency-system Plan/112). It still auto-wires to
      `capability_context_read` per `engine.py:85`.
  - [ ] `search(query, kind=None, limit=20)` — role `transform`. Ranks the merged
        corpus (static doc manifest + live SessionDB entries) by BM25, returns
        `data={matches: [{id, kind, title, score, snippet}], cursor}` (≤20 items + an
        opaque cursor), and sets `next_suggested_tools=["capability_context_describe"]`.
  - [ ] `describe(ids, view="summary")` — role `transform`. Accepts a list of ids,
        returns `data={views: [{id, summary, preview}]}` (NOT full bodies), and sets
        `next_suggested_tools=["capability_context_read"]`.
  - [ ] `read(id)` — role `transform`. Returns the full body of ONE id
        (`data={id, kind, body}`) and sets `next_suggested_tools` to *actionable*
        capabilities relevant to the doc's `kind` (e.g. a discipline doc points to
        `capability_develop_checklist`).
- [ ] Every `ContextCapability` verb returns through the Spec 001 `ToolResult`
      envelope **exactly as 001 defines it** — fields
      `ok`, `data`, `warnings`, `next_suggested_tools`, `error`
      (`agency/Plan/001…/spec.md:184-216`); the payload lives under **`data`**, NOT
      under a legacy `result` key (`result` is the unwrapped key `_wire` strips
      today at `engine.py:73`). The auto-wired tool name is `capability_context_<verb>`
      per `engine.py:85`.
- [ ] `agency/capabilities/develop.py:140` (`reference`) no longer hardcodes the
      doc body: it either (a) is removed and its 3 `REFERENCES` strings migrate
      into the context manifest as `kind="discipline-howto"`, or (b) thin-delegates
      to `ctx.call("context", "read", id=...)`. The 3 docs remain reachable; a
      test proves `context.search("best-practices")` finds `best-practices`.
- [ ] `agency/context/index.py` opens a SQLite SessionDB (WAL mode, `busy_timeout`)
      with an FTS5 virtual table; `put(kind, title, body) -> id` stores an entry and
      `search(query, kind, limit)` / `get(id)` read it. The multi-writer contract is
      pinned (see `## Design` → SessionDB): the **engine** owns first-create + schema
      migration under a transaction; the hook subprocess opens read-write but never
      `CREATE`s — it `put`s into an already-initialised schema, retrying on
      `SQLITE_BUSY` up to `busy_timeout`. Survives the two concurrent writers
      (the hook subprocess + the engine MCP).
- [ ] `agency/context/summarize.py` turns a large tool output into
      `{summary, stored_id, bytes_in, bytes_out}` — body goes to the SessionDB,
      a token-tiny summary comes back.
- [ ] `agency/context/manifest.py` builds/loads a manifest of the static doc corpus
      (`docs/**`, the 3 develop references) into the same SessionDB so the triad
      searches one merged index. Rebuild is **mtime-gated at `SessionStart`** (and a
      lazy first-`search` rebuild as a fallback, since `SessionStart` here only
      attaches) — matching the exemplar's sha256/mtime drift guard (Plan/111).
- [ ] `hooks/hooks.json` (repo ROOT) declares the hook entry points this spec
      adopts: `PostToolUse` → `agency/hooks/ctx_route.py` (output capture),
      `PreToolUse` → `agency/hooks/ctx_route.py` (routing; no-op default this spec),
      `SessionStart` → `agency/hooks/ctx_session.py` (attach DB), and
      `UserPromptSubmit` → `agency/hooks/ctx_session.py` (capture user decisions).
      It does **not** declare a `PreCompact` snapshot handler — that pair is deferred
      (see `## Why` and Open Questions).
- [ ] `agency/hooks/ctx_route.py` reads a hook event JSON on stdin, and on
      `PostToolUse` for an output over the threshold (provenance + value TBD by the
      measured trace; see `## Design` → threshold) replaces the output with a summary
      via `agency/context/summarize.py`, emitting the Claude-Code hook decision JSON
      on stdout. Exits 0 and is a no-op (passes the output through unchanged) for
      small outputs or on any internal failure — **a hook must never break the
      session.**
- [ ] `skills/ctx-insight/SKILL.md` + `commands/ctx-insight.md` (repo ROOT) document
      the local `/ctx-insight` surface: query the SessionDB index for what was routed
      out of context this session. It is **our own file-direct reader over the SQLite
      DB** (no listener, no HTTP), which deliberately diverges from upstream
      context-mode's local web-UI `/ctx-insight` — stated as such. Local-only; no
      network egress.
- [ ] **Measured token before/after** (see `## Design` → Token economics): a real
      trace of "find and read the `best-practices` doc" is captured with a token
      counter (not asserted from memory), the before/after numbers are pasted under
      `## Evidence`, and the savings claim in the doc matches the trace (no bare
      "97%"/"98%" assertion without the trace).
- [ ] `tests/test_context_capability.py` + `tests/test_context_hooks.py` pass;
      `pytest -q` stays green (was 56 passing). Hook tests cover: `ctx_route.py`
      summarizes an over-threshold fixture and stores it; small output passes
      through; `search → describe → read` round-trips an id stored by the router;
      the triad degrades gracefully (returns `ok=True` with empty matches) when the
      SessionDB is **absent**; AND the triad degrades gracefully when the SessionDB
      is **present but locked/corrupt mid-session** (returns `ToolResult.failure(
      BOUNDARY_ERROR, ...)` per Spec 001's `ErrorCode`, never an unhandled raise).
- [ ] No source from the external `context-mode` plugin is copied into the tree.
      **Resolved (Open Q-1 = reimplement):** we reimplement the pattern in stdlib
      `sqlite3` + the engine's own primitives so the triad and the hook share one
      in-process SessionDB; the marketplace plugin stays a documented opt-in
      companion only (ELv2 makes a runtime dependency license-toxic for an opt-in
      plugin). No `context-mode` API is consumed.

## Design

### How it composes with code-mode and the ToolResult envelope (Spec 001)

Two orthogonal axes, one loop:

| Axis | Owns | Mechanism | Where |
|---|---|---|---|
| **schema-side context-mode** (existing) | tool *schemas* | `CodeMode()` + `search`/`get_schema`/`execute` | `engine.py:91-95` |
| **output-side context-mode** (this spec) | tool *outputs* | SessionDB/FTS5 + `ContextCapability` triad + the `PostToolUse`-capture/`SessionStart`-attach hooks | `agency/context/*`, `agency/hooks/*`, `capabilities/context.py` |
| **ToolResult envelope** (Spec 001) | the *seam between steps* | `ok` + **`data`** + `warnings` + `next_suggested_tools` + `error` | `engine.py:_wire`, all verbs |

> **Hard dependency, stated plainly:** this spec does not invent its own wire
> shape. Spec 001's `ToolResult` **is** the wire shape — its `to_dict()` emits
> `{ok, data, warnings, next_suggested_tools, error}` (`001:209-216`). Every verb
> sketch below uses **`data`**. The legacy `result` key that `_wire` strips today
> (`engine.py:73`) is gone here.

The triad is an ordinary self-registering capability: `discover()` finds it,
`Engine._wire` (`engine.py:61-89`) auto-wires `capability_context_search` /
`_describe` / `_read` from the verb signatures, `CodeMode` defers their schemas
like every other tool. No core change — the engine treats `context` exactly like
`develop` or `reflect`. The triad reaches the SessionDB through `ctx` (the index is
constructed once and handed to the capability via the engine's injector seam,
mirroring how `jules_client`/`vcs_backend` are injected in `engine.py:55-56`).

`next_suggested_tools` is the glue. Spec 001 puts the field on the `ToolResult`
envelope; this spec is its first real consumer — `search` points at `describe`,
`describe` points at `read`, `read` points at an actionable capability. That
collapses the orienting round-trips that the bare dict at `engine.py:74` forces
today. **This glue presumes 001 Open Q-2 resolves in favour of surfacing the
envelope (or at least `next_suggested_tools`) at `_wire`** — see Open Questions;
it is this spec's true critical-path blocker.

### ContextCapability verbs (the triad)

```
search(query, kind?, limit=20)  -> ToolResult(ok=True, data={matches:[{id,kind,title,score,snippet}], cursor},
                                              next_suggested_tools=["capability_context_describe"])
describe(ids, view="summary")    -> ToolResult(ok=True, data={views:[{id, summary, preview}]},
                                              next_suggested_tools=["capability_context_read"])
read(id)                         -> ToolResult(ok=True, data={id, kind, body},
                                              next_suggested_tools=<actionable caps for that kind>)
```

`kind` partitions the merged corpus: `doc` (static `docs/**`), `discipline-howto`
(the migrated develop references), `tool-output` (live session payloads routed by
the hook). **Why no event taxonomy:** the exemplar's Plan/108 carried a
26-category `event_map.py` *because* it bridged outputs into a Spec 100 SessionLog
event stream (the live context-mode repo lists 23 such categories). Agency has no
SessionLog to map into, so this spec deliberately drops the event taxonomy and
uses just these three `kind`s. `search` never returns bodies; `describe` returns
summaries/previews; only `read` pays for a full body — and only for one id. This
is the same narrow→narrow→pay funnel the FastMCP search/get_schema/execute loop
uses, applied to *content* instead of *schemas*, mirroring Plan/112's view ladder.

### The hook map (output-side, Claude-Code layer)

`hooks/hooks.json` (repo ROOT). Roles below match the **verified live
context-mode contract** (WebFetched 2026-05-27), restricted to the slice this
spec adopts:

| Hook | Handler | Job (this spec) |
|---|---|---|
| `PreToolUse` | `ctx_route.py` | upstream role = sandbox **routing** before a tool runs; **no-op default this spec** (routing hardening is a follow-up) |
| `PostToolUse` | `ctx_route.py` | capture the tool's output: if over threshold, store body in SessionDB, return summary + handle |
| `SessionStart` | `ctx_session.py` | upstream role = **restore** after compaction/resume; here = **attach** the SessionDB + mtime-gated manifest rebuild |
| `UserPromptSubmit` | `ctx_session.py` | upstream role = capture **user decisions/corrections**; here = record them into the SessionDB as `kind="decision"` for `/ctx-insight` recall |

> **`PreCompact` is intentionally absent.** Upstream uses it to build an ≤2 KB
> priority-tiered snapshot that `SessionStart` then restores — the
> snapshot→restore checkpoint pattern that the-agency-system Plan/120
> (`smart-compaction-checkpoints`) implements as a full 2-session spec
> (`pick_richest`, decision regex, `compose_digest`). This spec does **not** ship a
> `PreCompact` handler and does **not** restore checkpoints; doing so would either
> half-implement the pattern (silently losing continuity) or balloon scope. It is
> deferred to a follow-up that adopts Plan/120's depth honestly.

Contract details:
- `ctx_route.py` is the I/O shape of a Claude-Code hook: a JSON event on stdin, a
  decision JSON on stdout, exit 0. On *any* exception or a missing SessionDB it
  emits a pass-through decision (the original output, unchanged) and exits 0.
  Store failure must never break the orchestrator.
- Local-only: the SessionDB is a file; `/ctx-insight` reads it directly (no
  listener). No port is bound — this diverges from upstream's local web UI by
  design (Open Q-4). Claude-Code hooks are stdin/stdout; none require HTTP.

### The SessionDB (in-process shared store)

`agency/context/index.py` is a thin SQLite wrapper:
- `CREATE VIRTUAL TABLE entries USING fts5(kind, title, body)` + a side table for
  `id`, `created_at`, `bytes`.
- WAL mode + `busy_timeout` so the hook subprocess (a separate process from the MCP
  server) and the engine can both write. Pure stdlib `sqlite3`; no new dependency.
- **Multi-writer write-ordering contract** (the question Plan/108 deferred to an
  ADR; pinned here because we own the store): the **engine** is the sole creator —
  on `SessionStart`/first construction it opens the DB, runs `CREATE TABLE IF NOT
  EXISTS` + the FTS5 schema inside one transaction, and sets `PRAGMA
  journal_mode=WAL`. The **hook subprocess never `CREATE`s**; it opens read-write
  against the already-initialised schema and `put`s, retrying on `SQLITE_BUSY` for
  up to `busy_timeout`. First-write race is resolved by `IF NOT EXISTS` +
  transaction so two processes hitting an uninitialised FTS5 table cannot
  double-create. If the hook opens before the engine has created the schema, it
  no-ops (pass-through) rather than `CREATE`-ing a divergent table.
- DB path under the plugin data dir (`$CLAUDE_PLUGIN_DATA` or `~/.agency/`), one DB
  per session keyed by the Claude session id from the hook event. The filename is
  **distinct** from any context-mode DB so an installed companion plugin never
  shares or fights our file.

The *same* `Index` object backs both `PostToolUse` storage (process A, the hook)
and `ContextCapability.search/read` (process B, the engine MCP). That single
shared corpus is the point: there is one canon for "what left the window," reachable
both from `/ctx-insight` (browse) and from `capability_context_*` (query in-flow).
This in-process sharing is exactly why the vendor decision must be **reimplement,
not depend** — a bridge-only dependency could not back `read(id)` without a
network hop into context-mode's HTTP surface.

### Token economics — the measured trace

Task: *find and read the `best-practices` development doc, then act on it.*

**Before** (today's tree, code-mode boot already applied):
- Boot tool surface with `CodeMode`: ~400–500 tokens (the `<500` budget in
  `docs/vision/CORE.md:42`; without code-mode the bare tool list is ~34k — that
  win is already banked and not re-counted here).
- `develop.reference(topic="best-practices")` returns the full ~500-token body
  (`develop.py:103-110`) — and the model had to *already know* the topic string;
  there is no discovery path.
- The bare-dict return (`engine.py:74`) carries no `next_suggested_tools`, so the
  model spends an orienting round-trip (~300 tokens of re-`search`/`get_schema`)
  to find the actionable next capability.
- **Before total ≈ 1,300 tokens** for one doc + one orientation, and the rest of
  `docs/**` stays undiscoverable.

**After** (this spec + Spec 001 envelope):
- `context_search("best-practices")` → ~50-token id list, `next` → `describe`.
- `context_describe(ids=["best-practices"])` → ~120-token preview, `next` → `read`.
- `context_read(id="best-practices")` → ~500-token body, `next` → the actionable
  capability (no orienting round-trip; the envelope already named it).
- **After total ≈ 670 tokens** AND the whole `docs/**` corpus is now searchable.

For a *re-read of an already-seen large output* (the hook path), the win is larger:
a `PostToolUse` on a 50-KB log dump (~12k tokens) returns a ~150-token summary +
handle — the body never re-enters context; the model `context_read`s only the
slice it needs. **Every numeric figure above (the ~1,300/~670 totals, the ~12k/~150
hook figures, and any percentage) is an UNMEASURED placeholder.** The Done-When
gate requires a real counted trace (a tokenizer over the actual `ToolResult` JSON
for each step) before any number is asserted in prose or the disambiguation doc.
The spec asserts the *method*, not the percentage — do not ship "97%/98%" unbacked.

### The PostToolUse threshold (needs a measured value)

The capture threshold is **not asserted**. Prior art disagrees: the live
context-mode repo routes at **5 KB** with intent-driven filtering; Plan/108 cited
context-mode's ">2 KB Think-in-Code" rule; Plan/114's read-cache uses
token-optimizer's 50 KB / 2,000-line / 1,000-token-minimum thresholds. The
implementation ships a configurable default and the chosen value is justified by
the same measured trace that backs the token numbers — not picked from memory.

## Files

> The research drafts disagree on the package root (`agency_mcp` in the exemplar's
> tree vs `agency` here). **This repo is `agency/`.** All paths below use `agency/`.

- **Create**:
  - `agency/capabilities/context.py` — `ContextCapability` (search/describe/invoke).
  - `agency/context/__init__.py` — re-exports `Index`, `summarize`, `build_manifest`.
  - `agency/context/index.py` — SQLite + FTS5 SessionDB (WAL, busy_timeout, multi-writer).
  - `agency/context/summarize.py` — large-output → summary + stored id.
  - `agency/context/manifest.py` — build/load the static `docs/**` corpus into the index.
  - `agency/hooks/hooks.json` — the 5 hook entry points.
  - `agency/hooks/ctx_route.py` — PreToolUse/PostToolUse stdin→stdout router.
  - `agency/hooks/ctx_session.py` — SessionStart/PreCompact/UserPromptSubmit handlers.
  - `skills/ctx-insight/SKILL.md` — the `/ctx-insight` local index surface.
  - `commands/ctx-insight.md` — the slash command.
  - `tests/test_context_capability.py`, `tests/test_context_hooks.py`.
  - `docs/vision/specs/context-mode-output-side.md` — disambiguates the two
    "context-mode"s; the both-halves lifecycle diagram.
- **Modify**:
  - `agency/engine.py` — inject the shared `Index` into the `context` capability via
    the existing injector seam (`engine.py:55-56`); no change to `_wire` shape
    beyond what Spec 001 lands.
  - `agency/capabilities/develop.py` — drop/redirect `reference` (`develop.py:139-145`);
    migrate the 3 `REFERENCES` bodies into the manifest.
  - `agency/.claude-plugin/plugin.json` — register `hooks/hooks.json` and the new
    command (additive; the external plugin stays an opt-in companion, not a hard dep).
- **Move / Delete**: none beyond the `reference` redirect above.

## Open Questions / Needs Research

1. **Vendor vs depend.** Do we (a) reimplement the output-side pattern in-tree
   (stdlib `sqlite3` + our own router) so the engine owns the SessionDB and the
   triad reads it directly, or (b) depend on the marketplace `context-mode` plugin
   and only *bridge* to its `/ctx-insight`? The exemplar (Plan/108) chose (b)
   strictly (copies no source). **Recommendation to confirm:** (a) — because the
   triad must read the *same* corpus in-process, a bridge-only approach can't back
   `context_invoke` without a network hop. Decide before code.
2. **License.** The external `context-mode` is Elastic License 2.0. Reimplementing
   the *pattern* (not the code) is fine, but confirm we copy no source and that an
   optional runtime *dependency* (if (b)) is compatible with the agency plugin's
   license. Blocker for the vendor decision.
3. **The name.** "context-mode" already means schema-side progressive disclosure in
   this repo (`docs/guide/usage.md:36,61`, `CORE.md:11-13`). Adopting the external
   plugin's name for the output side risks confusion. Options: keep both under one
   "context-mode" umbrella with "schema-side"/"output-side" qualifiers (current
   plan), or rename the new half ("session-index" / "output-mode"). Resolve in the
   new doc before merging.
4. **Local HTTP port policy.** The external plugin exposes `/ctx-insight` over local
   HTTP. Do we need a port at all, or can `/ctx-insight` read the SessionDB file
   directly (no listener)? **Recommendation:** file-direct, no port — simpler and
   removes the egress question entirely. Confirm against any Claude-Code hook
   constraint that needs the HTTP shape.
5. **Real token numbers.** The Before/After in `## Design` are reasoned estimates,
   not a trace. Needs a counted run (tokenizer over the actual `ToolResult` JSON for
   each step) before the doc states a percentage. Do not ship "97%"/"98%" unbacked.
6. **PreToolUse read-cache (deferred).** The research (Plan/114) proposes a
   `difflib.unified_diff` read-cache on `PreToolUse` for repeated file reads. Worth
   it, but a separate concern from the output-index — propose splitting into a
   follow-up spec rather than expanding this one.
7. **Manifest staleness.** When does `manifest.py` rebuild the static `docs/**`
   index — every `SessionStart`, on mtime change, or on demand? Cheapest correct
   answer needed (proposed: mtime-gated rebuild at `SessionStart`).

## Evidence

- Boot win already banked: `agency/engine.py:91-95` (`CodeMode()` transform);
  `<500 tokens` / `<4 KB` boot budget at `docs/vision/CORE.md:42` and
  `docs/guide/usage.md:57-64`.
- Leak 1 (bare dicts, no `next_suggested_tools`): `agency/engine.py:73-74`.
- Leak 2 (single hardcoded doc loader): `agency/capabilities/develop.py:139-145`
  (`reference` verb) over `develop.py:86-111` (the 3-entry `REFERENCES` dict).
- Leak 3 (no output-side seam): no `agency/hooks/` and no `agency/context/` exist
  (confirmed by `ls`; the engine has no `PostToolUse` integration).
- Existing "context-mode" meaning (the collision): `docs/guide/usage.md:36,61`,
  `docs/vision/CORE.md:11-13`, `docs/guide/concepts.md:74`.
- Envelope deliberately deferred (so Spec 001 must land it):
  `docs/vision/specs/capability-base.md:87-91`; opt-in note in
  `docs/EXTENSION-PLAN.md:73-74`.
- Self-registration + auto-wire seam this capability rides:
  `agency/engine.py:48-52` (`discover()` + register/extend), `engine.py:61-89`
  (`_wire`), `engine.py:55-56` (injector seam for boundary objects).
- The exemplar to match/extend for THIS tree: `the-agency-system` Plan/108
  (5-hook contract, `/ctx-insight`, graceful-offline, multi-writer SessionDB ADR);
  triad shape from research `code-context-mode/SPEC.md:39-47` and
  `capability-specs/specs/context-mode.md`.
- `_ingest.md` ledger (glanced): research `code-context-mode/_ingest.md:25-32`
  enumerates the context-mode/FTS5/hook/triad sources.
