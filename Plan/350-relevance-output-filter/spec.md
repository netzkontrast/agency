---
spec_id: "350"
slug: relevance-output-filter
status: draft
last_updated: 2026-06-20
owner: "@agency"
vision_goals: [2]
depends_on: ["073", "334", "336", "337"]
domain: shell
wave: program-master
parent_spec: "337"
---

# Spec 350 — Generalized relevance filter (find the interesting part of any output)

> Owner directive: *"a generalized Filter class that can be configured to find the
> interesting part of an output — for starters to only show activities that are of
> interest (maybe keywords or patterns we can make explicit). The filter should
> also be used in shell and tool-call returns."* One configurable filter, three
> consumers (jules activities · shell · captured tool-calls), zero new subsystem —
> it extends the shipped Spec 337 filter registry with a **relevance** strategy.

## Why

Three surfaces return verbose output where only a fraction is interesting, and
none can be told *"keep the parts matching THESE patterns"*:

- **jules.activities** trims every activity to a 280-char summary preview
  (`_activity_summary`) — the bug Spec 348's sibling fix (`full=True`, shipped
  this branch) exposed: you either get a lossy preview or the raw firehose, never
  *"the agentMessaged + failure lines, in full, the heartbeats dropped."*
- **shell output** and **captured tool-calls** route through Spec 337's
  `_FILTER_PROFILES` / `capture_filter`, but those strategies are **structural**
  (`head+tail`, `count+head`, `fields`, `names`, `stat`) — positional, not
  content-aware. They can keep the first 20 lines; they cannot keep *the 3 lines
  that mention `ERROR`* out of 2000.

The owner wants a **content-aware relevance filter**: configurable
include/exclude patterns that extract the signal, reused across all three sites.
This is also the exact mechanism the Spec 348/349 review (PR #222) requires for
its token-budget finding — *"return a token-bounded summary, not the full
ledger"* — so 350 is the shared primitive that closes both.

## Design — one filter, a config registry, three call sites

### 1. The filter is a pure strategy added to Spec 337 (not a new subsystem)

`capture_filter(cmd, out, *, tool, spec)` (Spec 337, `shell/_main.py`) already
dispatches on a `spec` strategy string. 350 adds one strategy — **`relevance`** —
backed by a pure helper `relevance_filter(text, profile) -> dict`:

```
relevance_filter(text, profile) -> {
    "kept":    str,    # the interesting slice (matched lines + context)
    "matched": int,    # how many lines/sections matched
    "elided":  int,    # how many were dropped  (NEVER silent — CLAUDE.md #9)
    "locator": str,    # how to fetch the full text (the Spec 336 cursor)
}
```

A `profile` is `{include: [pattern...], exclude: [pattern...], context: int,
budget: int, unit: "line"|"section"}`:

- **include** — keep a unit if any include pattern matches (regex; empty include
  = keep all, then apply exclude). Each kept unit carries `context` neighbour
  lines.
- **exclude** — drop a unit if any exclude pattern matches (applied after
  include — exclude wins, so `include:["WARN"] exclude:["WARN: deprecated"]`
  works).
- **budget** — a token cap (reuse the Spec 337 token-bounding); when the matched
  set exceeds it, keep the highest-signal units and report the rest as `elided`
  with the `locator` — **truncate-with-a-pointer, never silently** (rule #9: a
  dropped tail is reported, full is one fetch away).
- **unit** — `line` (grep-like) or `section` (a matched line plus its block, for
  structured output like a stack trace or a JSON object).

Pure + no execution → **hook-ready**, exactly like the existing `shell.filter`
the search flags "hook-ready". Same fail-open contract as Spec 337: a bad pattern
degrades to the structural fallback, never raises on the capture path.

### 2. Config registry — `filters:` profiles (Spec 334), open set

A `filters:` config section holds **named profiles**, per consumer, user-editable
in `.agency/config.yaml` and overridable per call:

```yaml
filters:
  activities:                       # jules.activities default profile
    include: ["agentMessaged", "sessionFailed", "error", "blocked"]
    exclude: ["heartbeat", "progressUpdated"]
    context: 0
    budget: 1500
  shell:                            # shell / Bash capture
    exclude: ["^\\s*$", "DEBUG", "^\\s*at "]   # blank lines, debug, JVM stack noise
    budget: 800
  toolcall:                         # captured tool-call returns
    include: ["error", "warning", "FAIL", "Traceback"]
    context: 2
    budget: 600
```

This needs the **list-valued `_config` branch** (the same one Spec 349 §6 calls
for — a shared dependency; whichever lands first builds it). Profiles are an open
set (CLAUDE.md #8): a consumer names a profile, defaults ship seeded behind an
`AGENCY-DRIFT: filter-profiles` tag, users add their own. A graph-override read
path (like `shell.define`) is the deferred follow-up, mirroring Spec 337's own
deferred `FilterProfile` override.

### 3. The three call sites (single source — the owner's "generalized")

| Site | Wiring | Default profile |
|---|---|---|
| **jules.activities** | a `filter="<profile>"` arg → `relevance_filter` over the activity stream (kinds + body); the shipped `full=True` still returns raw, unfiltered | `filters.activities` |
| **shell / Bash capture** | a `relevance:<profile>` entry in `_FILTER_PROFILES`; `capture_filter` dispatches to `relevance_filter` | `filters.shell` |
| **captured tool-call returns** | `engine._default_hook_handler`'s PostToolUse capture routes the return through `relevance_filter` before the Spec 336 `filtered` view | `filters.toolcall` |

One helper, three thin call sites — adding a fourth consumer is a profile + a
one-line dispatch, never a new filter.

### What this spec does NOT do

- No new storage — reuses the Spec 336 `toolcalls.db` `filtered` view + the cursor
  locator.
- No LLM relevance — patterns are deterministic (regex/keyword); an LLM-scored
  relevance mode is a documented later strategy behind the same `profile` shape,
  not this slice.
- No silent truncation — `elided` + `locator` are always returned (CLAUDE.md #9);
  `budget` caps the *return*, never the stored capture (Spec 348 review Sev3#5:
  graph/store stays full, the wire is bounded).

## Acceptance (Gherkin)

```gherkin
Scenario: relevance keeps the matching lines and reports what it dropped
  Given output of 2000 lines where 3 contain "ERROR"
  And a profile include=["ERROR"] context=1 budget=500
  When I relevance-filter the output
  Then the kept text contains the 3 ERROR lines with one neighbour each
  And elided reports the ~1994 dropped lines (nothing is silently cut)
  And a locator to the full text is present

Scenario: exclude wins over include
  Given a profile include=["WARN"] exclude=["WARN: deprecated"]
  When I filter text with both a real WARN and a "WARN: deprecated" line
  Then the real WARN is kept and the deprecated line is dropped

Scenario: the same filter serves all three sites (single source)
  Given the filters.activities, filters.shell, filters.toolcall profiles
  Then jules.activities, shell capture, and tool-call capture all route through
       the one relevance_filter helper

Scenario: a config profile is user-overridable
  Given filters.shell.exclude includes "DEBUG" in .agency/config.yaml
  When shell output containing DEBUG lines is captured
  Then the DEBUG lines are dropped from the filtered view

Scenario: budget bounds the return but not the stored capture (review Sev3#5)
  Given a whole-repo scan output far over the budget
  When it is relevance-filtered for the wire
  Then the return is within budget with an elided count + locator
  And the full output remains retrievable from the Spec 336 store

Scenario: a bad pattern fails open to the structural fallback
  Given a profile with an invalid regex
  When capture_filter runs on the hook path
  Then it degrades to the Spec 337 structural fallback and never raises

Scenario: jules.activities full=True bypasses the filter
  When I call jules.activities(full=True)
  Then the raw untrimmed, unfiltered activities are returned
```

## Followup — Implementation Status (2026-06-20)

### Slice 1 — SHIPPED (steward run, 2026-06-20)

**Done:**
- `agency/_relevance.py` — pure `relevance_filter(text, profile) -> dict` with
  include/exclude/context/budget logic; returns `{kept, matched, elided, locator}`;
  fail-open on bad patterns (CLAUDE.md #9). 7/7 acceptance scenarios green.
- `agency/capabilities/shell/_main.py` — `relevance:<JSON>` strategy wired into
  `_apply_filter`; dispatches to `relevance_filter`; fail-open on bad profile JSON.
- `agency/capabilities/jules/_main.py` — `filter: str = ""` param on `activities`;
  filters by `kind + summary` text when `full=False`; adds `filter_applied` to result;
  `full=True` bypasses filter entirely (existing escape hatch preserved).
- `tests/acceptance/features/relevance.feature` + `tests/acceptance/test_relevance.py`
  — 7 Gherkin scenarios covering pure helper, `_apply_filter` integration,
  `jules.activities` filter, and `full=True` bypass.

### Slice 2 — SHIPPED (steward run, 2026-06-21)

**Done:**
- `agency/_relevance.py` — `_DEFAULT_FILTER_PROFILES` dict (3 seeded entries: activities,
  shell, toolcall) with `# AGENCY-DRIFT: filter-profiles` tag; `load_filter_profile(name,
  path=None) -> dict` reads raw `_config._read()["filters"][name]` (OPT-IN: absent section
  → `{}`, so no existing behavior changes without user opting in via config.yaml).
- `agency/capabilities/jules/_main.py` — `activities(filter=)` now tries a named config
  profile lookup (via `load_filter_profile(filter)`) before treating the string as a keyword
  include; backward-compatible (unknown names fall through to `{"include": [filter]}`).
- `agency/capabilities/shell/_main.py` — `capture_filter` applies `load_filter_profile("shell")`
  after structural `_apply_filter`, Bash-only (OPT-IN: only runs when user sets
  `filters.shell:` in config.yaml).
- `agency/engine.py` — `_default_hook_handler` PostToolUse path applies
  `load_filter_profile("toolcall")` to the `filtered` field after `capture_filter`
  (OPT-IN; fail-open on any error).
- 3 new Gherkin scenarios (10 total green, 1.96 s): named config profile drives
  `jules.activities`; `capture_filter` applies shell profile; PostToolUse applies
  toolcall profile.

**Still needed (Slice 3+):**
- Graph `FilterProfile` node override (mirrors Spec 337 structural profiles).
- LLM-scored relevance strategy.
- `filters:` section auto-generated in `config_scaffold` (with seeded `_DEFAULT_FILTER_PROFILES`
  as the initial content, so users see examples out of the box).
