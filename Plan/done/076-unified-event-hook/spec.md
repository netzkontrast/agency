---
spec_id: "076"
slug: unified-event-hook
status: shipped
state: done
last_updated: 2026-06-06
owner: "@agency"
depends_on: ["062", "064", "073"]   # hooks scaffold + the shell filter
research_first: true
affects:
  - hooks/                              # one dispatcher entry for all events
  - agency/                             # a hook-handler surface (capability or middleware)
estimated_jules_sessions: 0
domain: substrate
wave: 5
---

# Spec 076 — Unified event-hook interface (one hook, every event)

## Why

User directive (2026-06-06): *"describe the unified hook interface that we would
need to wire just ONE hook — for every event we want to capture."* Today the
plugin wires hooks per event (SessionStart, Spec 062/064). The user wants a
**single dispatcher** entry that captures every event and routes it — to
provenance (record the event in the graph), to `shell.filter` (trim tool-output
tokens — Spec 073's hook-ready filter), to loop-detection (`_middleware/loop`),
etc. — so adding event capture is configuration, not a new hook each time.

## Research first

Enumerate the Claude Code hook surface BEFORE designing:
- Which hook **events** exist (SessionStart, PreToolUse, PostToolUse, Stop,
  UserPromptSubmit, …), their **trigger semantics**, and their **payload shapes**
  (what JSON each delivers on stdin).
- The `hooks.json` schema + matcher model (Spec 064's `matcher`/`async` fields).
- Whether one hook command can subscribe to ALL events (a `matcher: "*"` /
  multi-event entry) or whether one entry per event is required (then the "unity"
  is a single dispatcher SCRIPT all entries call).
Record the findings as a graph reflection + cite the docs
(`https://code.claude.com/docs/en/plugins`).

## Research findings (2026-06-06 — `reflection:ca724b6c`)

Source: `https://code.claude.com/docs/en/hooks`.

- **~30 events** exist: SessionStart, Setup, UserPromptSubmit, UserPromptExpansion,
  PreToolUse, PermissionRequest/Denied, PostToolUse, PostToolUseFailure,
  PostToolBatch, SubagentStart/Stop, TaskCreated/Completed, Stop, StopFailure,
  PreCompact/PostCompact, SessionEnd, Notification, InstructionsLoaded, … .
- **Every payload** carries `session_id`, `transcript_path`, `cwd`,
  `hook_event_name` on stdin (POST body for HTTP hooks). Tool events add
  `tool_name` + `tool_input` (and output/failure variants). Many add
  `permission_mode`, `agent_id`/`agent_type`.
- **No top-level wildcard.** You MUST define one block per event name; within an
  event a `matcher: "*"`/`""` matches all occurrences. ⇒ **Unity = every event
  block invokes the SAME dispatcher script**; the agency-side handler surface is
  single (resolves OQ-1). `async: true` keeps capture off the critical path.

## Design (v1)

1. **`Event` node** (ontology) — `{name, session}` required. Recorded by the
   handler; linked `OBSERVED_DURING` to `AGENCY_INTENT` when that env is set
   (Spec 018 Win 3 integration — events during an intent become its provenance).
2. **Engine hook-handler surface (open set)** — `engine._hook_handlers` +
   `register_hook_handler(event_name, fn)`; a default handler records the Event
   and (for tool events) trims `tool_input`/output through `shell.filter`. A
   `hook_event(event)` **substrate tool** (no intent required — like
   `intent_bootstrap`) dispatches by `hook_event_name`. Handlers are registered,
   not hardcoded per event.
3. **CLI `agency hook`** — reads the event JSON from stdin, calls `hook_event`,
   prints a small ack. No `--intent-id` needed (uses `AGENCY_INTENT` if present).
4. **`hooks/dispatch`** — the single polyglot entry (run-hook.cmd pattern): reads
   stdin, pipes to `agency hook`. `async: true`.
5. **`install.generate()`** emits `hooks.json` wiring the capture-worthy events
   (UserPromptSubmit, PreToolUse, PostToolUse, Stop, SubagentStop, SessionEnd) to
   the one dispatcher. SessionStart keeps its specialized install hook
   (bootstrap, not capture); the dispatcher can absorb it in a followup.

## Done When

- [x] **Research report** (above) — the event catalogue + payloads + the
  one-dispatcher feasibility.
- [ ] **`hooks/dispatch`** — a single polyglot entry (Spec 064 pattern) wired for
  every event; it reads the event type + payload from stdin and routes to a
  handler.
- [ ] **An agency hook-handler surface** — the dispatcher calls into the engine
  (a `hook` verb or middleware) that, per event, records provenance and/or applies
  a filter/transform. Handlers are registered (open set), not hardcoded per event.
- [ ] `install.generate()` emits the unified `hooks.json` (all events → the one
  dispatcher) replacing the per-event entries.
- [ ] Tests: the dispatcher routes a synthetic event of each type to its handler;
  install regen produces one dispatcher entry.

## Migration

Extends the existing `hooks/` (Spec 062/064). The single dispatcher SUBSUMES the
session-start hook; old behaviour preserved (session-start routes through it).

## Open Questions

1. **One entry vs one dispatcher.** If Claude Code requires one `hooks.json` entry
   per event, "unified" = every entry invokes the SAME dispatcher script (resolved
   by research). Either way the agency-side handler surface is single.
2. **Token cost of capturing everything.** Capturing every event into the graph
   could be noisy; the handler decides what's worth recording (the dispatch-
   decision principle). Filtering (Spec 073) trims tool-output events.

## Evidence

- Spec 062 (`hooks/session-start`) + Spec 064 (`hooks/run-hook.cmd` polyglot +
  `hooks.json` matcher/async) — the scaffold this unifies.
- Spec 073 `shell.filter` (the hook-ready output trimmer).
- `agency/_middleware/loop.py` (a future hook consumer).
- Claude Code plugin docs (the hook event model — to be researched).

## Followup — Implementation Status (2026-06-06)

**Verdict:** Shipped (v1 — the dispatcher + handler surface + capture wiring)

### Done

- **`Event` node** (`ontology.py` core NODE_SCHEMAS) — `{name, session}`.
- **Engine hook-handler surface (open set)** — `Engine._hook_handlers` +
  `register_hook_handler(name, fn)` + `dispatch_hook(event)` routing by
  `hook_event_name` (exact handler wins, else "*" catch-all; never raises on a
  malformed event). `_default_hook_handler` records an Event, trims tool
  `tool_input`/`tool_response` through `shell._apply_filter` (Spec 073), and links
  the Event `OBSERVED_DURING` the active `AGENCY_INTENT` (Spec 018 Win 3) when set
  — events during an intent become its provenance.
- **`hook_event(event)` substrate tool** — no intent required (like
  `intent_bootstrap`); dispatches via `engine.dispatch_hook`.
- **CLI `agency hook`** — reads the event JSON from stdin, calls `hook_event`.
- **`hooks/dispatch`** — the single polyglot entry (run-hook.cmd pattern): pipes
  stdin to `agency hook`; best-effort, never fails the session.
- **`install.generate()`** emits a unified `hooks.json`: SessionStart keeps its
  specialized install hook; the capture events (PreToolUse, PostToolUse,
  SubagentStop + UserPromptSubmit, Stop, SessionEnd) all route to the ONE
  dispatcher (`async: true`; matcher where supported — research finding).
- **Tests** — `tests/test_hooks_dispatch.py` (9): event recording, tool-payload
  trim, open-set override, AGENCY_INTENT linkage, substrate tool, CLI stdin,
  install unified-wiring. check-drift clean (new `AGENCY-DRIFT: hook-events` tag);
  install regen committed; audit reflection `reflection:ca724b6c` (research).

### Deferred (followups)

- **More handlers** — loop-detection (`_middleware/loop.py`) + richer per-event
  filtering plug in via `register_hook_handler` (the surface is open); v1 ships
  the recording + tool-trim default only.
- **SessionStart absorption** — the dispatcher could subsume the install hook;
  v1 keeps session-start specialized (bootstrap ≠ capture) to stay non-breaking.
- **Noise budget** — capturing every PreToolUse/PostToolUse can be chatty; a
  future handler can apply the dispatch-decision principle to record selectively.
