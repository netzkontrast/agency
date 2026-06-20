---
spec_id: "336"
slug: toolcall-capture-export
status: drafted
last_updated: 2026-06-19
owner: "@agency"
vision_goals: [1, 2, 6]
affects:
  - agency/_capture.py
  - agency/_toolcalls.py
  - agency/engine.py
  - agency/capabilities/shell/_main.py
---
# Spec 336 — Lossless tool-call capture, no-truncate fidelity & self-improvement export

> **Status:** Drafted (2026-06-19). Extension spec — owner-directed.
> **Owner directives (verbatim intent):**
> - *"We don't ever want to truncate anything — except it has a pagination
>   function and the agent gets instructions to read the continuation that way.
>   Everything that just dumps into files — no truncate ever."*
> - *"Write pre and post tool calls in their own db."*
> - *"The stop hook gets an export of the data — the top-20 tool calls and
>   responses — with suggestions for new specs."*
> - *"Extend the shell capability and make it mandatory as a wrapper in hooks, so
>   we can filter the needed data from bash calls."*
>
> **Owner decisions (clarified before drafting):** bash wrapper = **capture &
> filter only** (execution unchanged); spec-suggestions = **heuristic now + LLM
> behind a config flag**; the tool-call DB is **local & ephemeral (gitignored)**.

## Why (evidence + doctrine)

Two forces collide in the current hook-capture path, and this spec resolves both:

1. **Truncation lies about what happened.** Spec 332-334's successor work shipped
   a no-truncate policy for captured data (`agency/_capture.py::keep_full`,
   CLAUDE.md rule 9 generalised). But "store full, warn if large" is only half the
   law: a *return* that is genuinely huge still needs a bounded response, and the
   honest way to bound a return is **pagination with read-continuation
   instructions**, never a silent cut. And anything **dumped to a file** must be
   full, always. This spec states the complete law and gives it a mechanism + a
   guard.

2. **Full capture in the durable graph bloats it.** The same policy made
   `_default_hook_handler` store the FULL pre/post tool payload as `Event` nodes
   in the bi-temporal graph (`.agency/session.db`). Measured: **1156 of 1217
   nodes (95%) were Events**, ~98% of them per-tool-call `PreToolUse`/`PostToolUse`
   — now carrying *full* payloads. That is the right DATA to keep, in the wrong
   PLACE: the durable provenance graph (committed, Spec 292/020) should hold
   Intents/Invocations/Gates, not every `Read`'s full response. The fix is not to
   truncate (we want all the data) but to **route the high-volume capture to its
   own ephemeral store**, and **distil the durable signal** out of it on session
   end.

Doctrine alignment: the graph stays the queryable spine (CLAUDE.md rule 1); the
no-truncate law is rule 9 completed; the self-improvement export is the
dogfooding loop (`reflect`/observation → new specs) made automatic; the shell
filter is the existing token-economy boundary (Spec 067) applied at capture time.

## Design

Four slices, each independently shippable.

### Slice 1 — No-truncate-or-paginate data fidelity

The complete law, in three rules:

- **Stored/captured data → FULL.** Already shipped (`keep_full`, warn-not-cut).
- **File dumps → FULL, always.** Anything written to disk is never truncated
  (extends CLAUDE.md rule 9 beyond the project index to every file write).
- **Bounded RETURNS → paginate, never cut.** A return that must be size-bounded
  returns a **page + a cursor + an explicit read-continuation instruction**, so
  the agent retrieves the rest deterministically. Truncation-without-continuation
  is forbidden.

Mechanism — extend `agency/_capture.py`:

```python
def paginate(items, *, cursor=0, page_size, kind="items") -> dict:
    """Return one page + the instruction to read the rest. NEVER drops data:
    the tail is reachable, not cut. Returns
    {page, cursor, next_cursor, total, remaining, read_more}."""
    # read_more = "" when exhausted, else a literal instruction:
    #   "{remaining} more {kind} — call again with cursor={next_cursor}."
```

Guard — a drift check (extends `scripts/check-drift`) that greps for `[:N]`
slices on captured/stored/file-written strings and flags any new one not routed
through `keep_full`/`paginate` (allow-list: hash prefixes, top-N, display width —
the documented non-data exceptions).

### Slice 2 — Separate ephemeral `.agency/toolcalls.db`

A dedicated SQLite store, **NOT the graph**, **gitignored** (local, ephemeral):

```
.agency/toolcalls.db          # append-only, full capture, never committed
  toolcall(
    id INTEGER PK, ts REAL, session TEXT, intent TEXT,
    phase TEXT,            -- 'pre' | 'post'
    tool TEXT,
    input_json TEXT,       -- FULL tool_input (keep_full)
    output_json TEXT,      -- FULL tool_response (keep_full)
    filtered TEXT          -- Slice-3 shell-filtered view (bash only), else ''
  )
```

`_default_hook_handler` for `PreToolUse`/`PostToolUse` writes the FULL record
**here** instead of recording an `Event` node in the graph. The graph keeps the
durable provenance (Invocations/Intents/Gates + the BoundaryUse moat audit, which
stays). Net effect: the durable, committed `session.db` stops growing by ~16 MB a
session, while **no data is lost** — it lives in full in the ephemeral store until
the Stop-hook export distils it.

A tiny module `agency/_toolcalls.py` owns the connection + schema + `record()` +
`top_n()` + `prune()`; no graph dependency, so it never touches the provenance
write path.

### Slice 3 — Shell-filter wrapper in the hook path (capture-only)

The shell capability is already the token-economy boundary (allowlist + output
filters, Spec 067). Extend it with a **capture filter** the hook path uses for
every Bash tool call:

- New surface: `shell.capture_filter(command, output) -> {command, filtered, …}`
  (reuses `_apply_filter`), the single place bash-call data is structured for
  provenance. **Mandatory** in the capture path: `_default_hook_handler`, when the
  tool is `Bash`, ALWAYS routes the call's command+output through it and stores
  the result in `toolcalls.filtered`.
- **Execution is unchanged** — Claude Code's `Bash` tool still runs the command;
  this only shapes the *captured data*. No allowlist enforcement on execution, no
  blocked commands (owner decision: capture & filter only).

The full raw command/output is still stored in `input_json`/`output_json`
(no-truncate); `filtered` is the cheap structured view the export prefers.

### Slice 4 — Stop-hook export: top-20 + new-spec suggestions

On `Stop`/`SessionEnd`, a handler reads `toolcalls.db` and produces a durable
**export artefact** — the self-improvement loop:

1. Rank the **top-20** tool calls (frequency × cost: repeated commands, repeated
   reads, longest outputs) with their (filtered) responses.
2. Generate **new-spec suggestions**:
   - **Heuristic (always):** repeated identical command ≥ N → "save a
     `shell.define` template / capability"; repeated reads of the same file →
     "consider an index/cache"; recurring long output → "add a filter"; a raw
     mutating tool with a verb shadow (from `_RAW_ROUTES`) → "route through the
     verb".
   - **LLM (optional, behind `toolcalls.suggest_via_llm`):** feed the top-20 to
     the Spec 092 `LLMClient` for richer proposals when a key is present.
3. Write the export to `.agency/sessions/<session>-toolcalls.md` (full, never
   truncated) **and** record a durable `ToolcallExport` Artefact in the graph
   (the distilled signal survives even as `toolcalls.db` is pruned).
4. Optionally `prune()` the ephemeral DB after a successful export.

Config keys (Spec 334 registry): `toolcalls.enabled` (default true),
`toolcalls.export_top_n` (default 20), `toolcalls.suggest_via_llm` (default
false), `toolcalls.prune_after_export` (default false).

## Slices (TDD)

1. **S1 — fidelity:** `paginate()` + file-dump-always-full + the drift guard.
2. **S2 — ephemeral store:** `agency/_toolcalls.py` + reroute pre/post capture off
   the graph into `toolcalls.db`; gitignore it; graph keeps BoundaryUse.
3. **S3 — shell capture filter:** `shell.capture_filter` + mandatory hook wiring
   for Bash; execution untouched.
4. **S4 — export:** Stop-hook reads top-20 → heuristic suggestions → export file +
   `ToolcallExport` Artefact; LLM pass behind the flag.

Per-slice: RED → GREEN → `pytest -q` → commit → push.

## Acceptance criteria

- No captured value, file dump, or bounded return ever silently drops data; large
  returns carry a working read-continuation cursor; the drift guard fails on a new
  un-routed `[:N]` on captured/file data.
- Pre/post tool calls land in `.agency/toolcalls.db` (full), **not** as graph
  `Event` nodes; `session.db` node growth per session drops to the durable
  provenance only; `toolcalls.db` is gitignored.
- Every captured Bash call carries a shell-`filtered` view; Bash execution
  behaviour is byte-for-byte unchanged (no blocked/allowlisted commands).
- On session end, an export artefact lists the top-20 calls+responses and ≥1
  heuristic spec suggestion, written in full to a file AND recorded as a durable
  `ToolcallExport` graph Artefact; the LLM pass runs only when the flag is set.

## Acceptance scenarios (Gherkin sketch)

```gherkin
Scenario: a bounded return paginates instead of truncating
  Given a result set larger than one page
  When it is returned through paginate(page_size=N)
  Then the first page carries exactly N items
  And a non-empty read_more instruction names the next cursor
  And reading every page yields the COMPLETE set with nothing dropped

Scenario: pre/post tool calls go to the ephemeral store, not the graph
  Given an engine with tool-call capture enabled
  When a PreToolUse and a PostToolUse for Bash fire
  Then two rows exist in toolcalls.db with the FULL command and output
  And no Event node was recorded in the provenance graph
  And toolcalls.db is gitignored

Scenario: a captured Bash call carries a shell-filtered view
  When a PostToolUse for Bash with a long output is captured
  Then the stored row's input_json/output_json hold the FULL data
  And filtered holds the shell capability's token-filtered view
  And the command itself was executed unchanged

Scenario: the Stop hook exports the top calls with spec suggestions
  Given several repeated commands recorded this session
  When the Stop hook fires
  Then an export file lists the top-20 calls + responses in full
  And it contains at least one heuristic new-spec suggestion
  And a ToolcallExport Artefact is recorded in the durable graph
  And the LLM suggestion pass ran only if toolcalls.suggest_via_llm is set
```

## Open questions

1. **Cursor format** — integer offset (simple, stable for append-only) vs opaque
   token (rotation-safe). Lean offset for v1.
2. **Retention** — does `toolcalls.db` rotate by size/age, or only prune on
   export? Lean prune-on-export-off-by-default (keep until the user opts in).
3. **Export destination** — file + graph Artefact both (recommended), or graph
   only? Both, so the human-readable report survives and the signal is queryable.
4. **Top-20 ranking** — frequency, cost (output size), novelty, or a blend? Start
   frequency × output-size; refine from dogfooding.
5. **BoundaryUse** — stays in the graph (it's the moat signal, low-volume) while
   the raw Event capture moves out — confirm no audit consumer reads the moved
   `Event` rows (only `dogfood.session` did; it reads BoundaryUse + the export).

## Followup — Implementation Status (SHIPPED 2026-06-19)

- **S1 ✅ (PR #188):** `agency/_capture.py::paginate` (page + cursor + read-more
  instruction; the walk reconstructs the full set). `scripts/check-no-truncate`
  guard wired into CI (advisory) — it caught **4 real stored-data truncations**
  (panel `subject`, persona `task`, prompt/recommend `request`) on first run, all
  fixed to `keep_full`. 3 fidelity scenarios.
- **S2 ✅:** `agency/_toolcalls.py::ToolcallStore` (gitignored `.agency/toolcalls.db`;
  `:memory:` for a bare engine). `engine.toolcalls` lazy; `_default_hook_handler`
  reroutes PreToolUse/PostToolUse to the store (no graph Event) — BoundaryUse moat
  stays. The **`toolcalls` capability** (`top`/`recent`/`stats`/`export`/`prune`) is
  the clear MCP surface; `ctx.toolcalls` accessor. 5 Spec 292 consumers updated
  (graph = lifecycle + provenance; tool stats via `toolcalls`).
- **S3 ✅:** `shell.capture_filter(command, output)` — a token-filtered VIEW; the
  hook routes every Bash call's data through it into the store's `filtered` column.
  Execution unchanged (capture & filter only). The FULL payload stays in
  `output_json`.
- **S4 ✅:** `toolcalls.export(top_n, apply, prune)` — heuristic suggestions
  (repeated command → shell template; repeated read → index; high-volume → filter)
  + an optional LLM pass behind `toolcalls.suggest_via_llm`; FULL report to
  `.agency/sessions/<session>-toolcalls.md` + a durable `ToolcallExport` artefact
  (schema'd). SessionEnd hook calls it (best-effort).
- **Evidence:** toolcalls (5) + hooks (29) + session_driver (9) + fidelity (3) +
  the Event-consumer suites green; install regen + drift + schema-coverage clean.
  PR #195. Config: `toolcalls.export_top_n` / `toolcalls.suggest_via_llm` (Spec 334).
