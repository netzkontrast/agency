---
spec_id: "337"
slug: per-tool-output-filters
status: drafted
last_updated: 2026-06-19
owner: "@agency"
vision_goals: [1, 2, 6]
affects:
  - agency/capabilities/shell/_main.py
  - agency/_toolcalls.py
  - agency/capabilities/toolcalls/_main.py
  - agency/capabilities/toolcalls/_export.py
  - agency/engine.py
---
# Spec 337 — Per-tool output filters (what to keep from each tool's output)

> **Status:** Drafted (2026-06-19). Extension of **Spec 336** — owner-directed.
> **Owner directive (verbatim intent):**
> *"Analyse tooluse please and create specs for the most often used tools and
> how and what we could filter from the output."*
>
> **Parent:** Spec 336 shipped the *mechanism* — an ephemeral tool-call store
> (`.agency/toolcalls.db`), a mandatory `shell.capture_filter`, and a Stop-hook
> export with heuristic new-spec suggestions ("high-volume → a filter"). Spec
> 336's filter is **generic** (`spec="head:20"` for every Bash call). Spec 337
> is the **realization of that "→ a filter" suggestion**: a per-tool /
> per-command-shape profile registry that distils each high-volume tool's output
> to its *signal*, not its first 20 lines.

## Why (grounded in dogfooded data)

A live session's tool-call census (`.agency/session.db`, 112 completed calls)
was analysed before drafting — the distribution, not a guess:

| Tool | Share | Output shape | `head:20` keeps the signal? |
|---|---:|---|---|
| **Bash** | **~70%** | heterogeneous (git / pytest / grep / ls / …) | **No** — depends on the command |
| Edit | 8% | a confirmation + context lines | partly |
| Read | 7% | the file body (often 100s of lines) | **No** — copies the file |
| ToolSearch | 5% | a `<functions>` schema dump | **No** — huge, recoverable |
| `mcp__github__*` | ~9% | a large JSON envelope | **No** — 2 fields matter |
| codegraph_* | 1% | source + call paths | partly |

The single `head:20` rule is **position-blind**: a `pytest` summary lives at the
*tail*, a `git diff`'s signal is its `--stat`, a `grep`'s signal is its *count*,
and a `Read`'s signal is its *locator* (the file is already on disk — copying its
body into the capture is the least useful thing to keep). Bash at 70% is itself
heterogeneous: a fixed rule cannot fit `git status`, `pytest`, and `ls` at once.

So: **the filter must be a function of the tool (and, for Bash, the command
shape), not a constant.**

## Non-negotiable: a filter is a DERIVED LENS, never a truncation (CLAUDE.md rule 9)

This spec touches captured data, so the no-truncate law governs it. To be
explicit, restated as the controlling invariant:

> The profile produces the **`filtered`** column — a cheap, structured VIEW the
> Stop-hook export prefers. The **lossless** payload always lands in
> `output_json` first, via `keep_full` (which *warns* on an unusually large
> value, never cuts). A profile can drop, reorder, or summarise **only in the
> derived view**. No profile may shrink, slice, or gate what reaches
> `output_json`. A `locator-only` Read profile keeps a 4-line address in
> `filtered` **while the full file body is retained verbatim in `output_json`.**

If a profile is ever the *only* place a tool's output is stored, that is the
defect — the lossless column is the record; the profile is the index to it.

## Design — a `FilterProfile` registry

A small, declarative, stdlib-only registry (no DSL — frugal floor). The wire
shape Spec 336 already wrote (`toolcall.filtered`) is unchanged; only its
*content* gets smarter.

### The value object

```
FilterProfile = {
    match:     (tool: str, shape: str | None),   # shape = Bash first-token / regex; None = any
    strategy:  Strategy,                          # how to distil (below)
    rationale: str,                               # WHY this is the signal (doctrine-grounded)
}
```

### Strategies (the closed, named set — extend by adding one, CLAUDE.md rule 8)

| Strategy | Keeps | For |
|---|---|---|
| `head:N` | first N lines | back-compat default; listings |
| `tail:N` | last N lines | `pytest` / build summaries (signal at the end) |
| `head+tail:N` | first + last N (elision marker between, with full-line count) | long logs with a head *and* a tail |
| `grep:<re>` | only lines matching `<re>` (+ total match count) | `pytest` FAILED/ERROR; `git status` porcelain |
| `count` | "<n> lines" / "<n> matches" only | `grep`/`rg`, `ls` of a big dir |
| `stat` | the leading `--stat`-style block, drop hunks | `git diff` / `git show` |
| `locator` | path + line-range + `sha16` of the body — **NO body copy** | `Read` (the file is on disk) |
| `fields:<a,b,…>` | the named top-level keys of a JSON envelope | `mcp__github__*` |
| `names` | the selected/returned identifiers only | `ToolSearch`, `codegraph_search` |

Every strategy bounds only the **derived view**. The elision marker is
`… N lines elided (full output retained in output_json) …` — it names where the
lossless copy lives, so the view never *looks* like the whole story.

### The initial profile table (top tools first — the 80% the census named)

| Tool | Shape (Bash first-token) | Strategy | Rationale |
|---|---|---|---|
| Bash | `git` + `status` | `grep:^[ MADRCU?]` | the porcelain file list is the signal; banner prose is not |
| Bash | `git` + `diff`/`show` | `stat` | the change *shape* (files × ±lines); hunks live in output_json |
| Bash | `git` + `log` | `head:N` | the recent oneline window |
| Bash | `pytest`/`python -m pytest` | `grep:(PASSED|FAILED|ERROR|passed|failed\| [0-9]+ (passed|failed))` + `tail:5` | failures + the summary line; never the dot stream |
| Bash | `grep`/`rg` | `count` + `head:N` | the count is the answer; a sample confirms |
| Bash | `ls` | `count` + `head:N` | "how many + a sample" |
| Bash | *(default)* | `head:20` | **unchanged** — Spec 336 back-compat |
| Read | — | `locator` | the file IS the content; keep its address |
| Edit / Write | — | `fields:file_path,verb` | the diff is already a graph `BoundaryUse`; don't re-copy the body |
| ToolSearch | — | `names` | the selected tool names; the schema dump is recoverable on demand |
| `mcp__github__*` | — | `fields:number,state,conclusion,mergeable_state,sha` | strip the envelope to the decision fields |
| codegraph_* | — | `head:40` | the flow header; full source is re-queryable |

`Bash (default) = head:20` makes Spec 337 a **strict superset** of Spec 336:
absent any matching profile, behaviour is byte-identical.

## Integration (extends, does not replace)

1. **`shell.capture_filter(command, output, *, tool="Bash", spec=None)`** — when
   `spec` is `None` (the hook path), resolve the profile from
   `(tool, first_token(command))`; an explicit `spec=` still wins (callers and
   tests keep full control). Return value shape (`"$ <cmd>\n<view>"`) unchanged.
2. **The hook capture path** (`engine._default_hook_handler`, Spec 336 S3) already
   routes Bash through `capture_filter`; Spec 337 widens it so **every** captured
   tool gets its profile-distilled `filtered` view (not just Bash) — still
   capture-and-filter only, execution untouched, `output_json` still `keep_full`.
3. **The export** (`toolcalls.export`, S4) renders the **`filtered`** column for
   its top-N table, so the self-improvement report is now high-signal per tool
   instead of 20 raw lines each.
4. **Definable, not frozen** — the registry seeds the table above but reads
   graph-defined overrides the same way `shell.define` already adds command
   templates (CLAUDE.md rule 8: a profile is data, not a magic constant). A
   project can add/override a profile without a code change.

## Acceptance (Gherkin — behaviour, not internals)

```gherkin
Feature: per-tool output filters distil the capture view losslessly

  Scenario: pytest output keeps failures + summary, not the dot stream
    Given a captured Bash call running "python -m pytest" whose output is
      200 dots then "3 failed, 197 passed"
    When the per-tool filter builds the view
    Then the view contains "3 failed, 197 passed" and the FAILED lines
    And the view does not contain the 200-dot progress stream
    And the FULL output is retained verbatim in output_json

  Scenario: a Read is captured by locator, never by body copy
    Given a captured Read of a 500-line file
    When the per-tool filter builds the view
    Then the view is the path + line-range + a 16-char body hash
    And the view does not contain the file body
    And the full file body is retained verbatim in output_json

  Scenario: an unknown command falls back to Spec 336 behaviour
    Given a captured Bash call whose first token has no profile
    When the per-tool filter builds the view
    Then the view equals the Spec 336 head:20 view exactly

  Scenario: a github MCP envelope is distilled to its decision fields
    Given a captured "mcp__github__pull_request_read" call returning a large
      JSON envelope with number, state and mergeable_state
    When the per-tool filter builds the view
    Then the view names those fields and omits the rest
    And the full envelope is retained verbatim in output_json

  Scenario: the export prefers the per-tool view
    Given captured calls across Bash, Read and a github MCP tool
    When toolcalls.export renders its top-N table
    Then each row shows that tool's distilled view, not raw output
```

## Scope / non-goals (frugal floor)

- **In:** the strategy set above, the seed profile table, the `capture_filter`
  resolution, widening capture-filter to non-Bash tools, the export render, the
  graph-override read path.
- **Out (YAGNI):** a per-tool *config UI*; ML/LLM-chosen filters (the S4 LLM pass
  already covers suggestion, behind its flag); streaming/incremental filters;
  filtering anything outside the `filtered` view (the lossless column is sacred).
- A profile that grows past a couple of strategies for one tool MAY promote to
  its own spec (the Spec 015→017/018/019 precedent) — not now.

## Followup — Implementation Status (Shipped 2026-06-20)

**Done (Slice 1 — shipped 2026-06-20):**
- `_FILTER_PROFILES` registry in `agency/capabilities/shell/_main.py` — 13 entries,
  first-match ordered; Bash shapes are regexes; non-Bash tools match by tool name
  (exact or prefix-wildcard `mcp__github__*`, `codegraph_*`).
- New strategies in `_apply_filter`: `head+tail:N`, `count+head:N`, `stat`,
  `fields:<a,b,...>`, `names` (added alongside existing head/tail/grep/count/last/full/lines).
- `_resolve_profile(tool, command)` — first-match lookup; returns the strategy string;
  falls back to `"head:20"` (Spec 336 back-compat).
- `capture_filter(command, output, *, tool="Bash", spec=None)` updated — `spec=None`
  auto-resolves via `_resolve_profile`; explicit `spec=` still wins; `locator` strategy
  handled inline (builds `path — N lines — sha16:...` from command + sha256 of body,
  no body copy); tool-appropriate header (`$ cmd` for Bash, `[Read path]` for Read, etc.).
- `agency/engine.py` `_default_hook_handler` widened — ALL captured tools route through
  `capture_filter(..., tool=tool_name, spec=None)` (not just Bash); Read extracts
  `file_path`, Edit/Write extract `file_path`, others stringify the input dict.
- 5 new Gherkin acceptance scenarios in `tests/acceptance/features/toolcalls.feature`
  + step implementations in `tests/acceptance/test_toolcalls.py` (all 10 scenarios green).
- S3 scenario updated: command changed from `ls -la /tmp` → `custom-script.sh --run`
  so the assertion `count("line") <= 20` holds under `head:20` fallback (ls now uses
  `count+head:20`).
- `scripts/check-drift` → NO DRIFT; `scripts/check-doc-drift --update` → 7 docs
  re-stamped (engine.py + capability-system sources changed).

**Still (deferred):**
- Graph-override read path for `FilterProfile` — analogous to `shell.define` for command
  templates; a graph-stored `FilterProfile` Artefact could override a seed profile without
  a code change (CLAUDE.md rule 8). Not blocking Slice 1 (the seed registry is the
  AGENCY-DRIFT: site that protects the live surface).
- `--fix-baseline` flag for `scripts/check_schema_coverage.py` (Spec 153 Slice 5;
  deferred from the 005 handover).
- Re-grounding the seed table against a larger session census (refinement note above).

**Evidence:**
- 10/10 `test_toolcalls.py` scenarios green; 14/14 `test_shell.py` green.
- `scripts/check-drift` → NO DRIFT (dormant-schemas gate also clean).
- `scripts/check-doc-drift` → 0 STALE after `--update`.
