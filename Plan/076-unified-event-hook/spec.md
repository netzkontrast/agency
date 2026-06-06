---
spec_id: "076"
slug: unified-event-hook
status: draft
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

## Done When

- [ ] **Research report** (above) — the event catalogue + payloads + the
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
