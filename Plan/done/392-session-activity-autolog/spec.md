<!-- agency-node: spec-392 -->
---
spec_id: "392"
slug: session-activity-autolog
status: done
state: done
last_updated: 2026-06-23
owner: "@agency"
vision_goals: [3, 9]
depends_on: ["286", "292"]
affects:
  - agency/_session_log.py    # the post-invocation append hook (new)
  - agency/engine.py          # enable_session_autolog() registers it on the seam
  - agency/__main__.py        # the production server opts in
domain: memory / provenance / session
wave: agency-self-teaching
---

# Spec 392 — Session activity auto-append (owner directive)

> Agency Self-Teaching Loop. Owner directive 2026-06-23: `document.session` writing
> `.agency/sessions/<intent>.md` is *wanted* — "keep and extend so the file gets
> **auto-appended with each call**." This is the grow/append twin of `document.session`'s
> on-demand snapshot.

## Problem

`document.session` renders a COMPLETE session Document on demand (Intent · Capability ·
Lifecycle · Memory, derived from the graph). It is a snapshot you must explicitly
request — there is no *live* record that grows as the session acts. The owner wants the
session file to update with every capability call, automatically.

## Approach (decoupled hook — no hot-path edit)

Spec 286-A3 already ships a `ResultProcessor.register_post_invocation` seam (hooks run
AFTER an Invocation's outcome is stamped). `agency/_session_log.py` registers ONE hook
that appends a single line per Invocation to a SEPARATE
`.agency/sessions/<intent>.activity.md`:

- **Append-only / grow-only** — never truncated (rule 9 — captured record never lies by
  omission); a separate file from `document.session`'s full snapshot, so neither clobbers
  the other.
- **Best-effort** — a write error NEVER fails a load-bearing verb (try/except → pass).
- **Opt-in** — `engine.enable_session_autolog()`; the production server (`__main__`) calls
  it. A bare test Engine stays file-side-effect-free unless it opts in.

## Acceptance

```gherkin
Scenario: each capability call appends one line and the log grows
  Given an engine with session autolog enabled
  When two capability verbs are invoked under one intent
  Then the intent's activity log exists with a line per call
  And the file is strictly longer after the second call (append-only growth)

Scenario: a bare engine writes no session file unless opted in
  Given an engine that did not enable session autolog
  When a verb is invoked
  Then no activity log file is written
```

## Decisions (WH(Y))

- **D1 — A decoupled post-invocation hook, not a hot-path edit.** The Spec 286-A3 seam
  exists for exactly this; registering a hook keeps `Registry.invoke` byte-stable. WHY:
  the moat's chokepoint stays unchanged; the feature is additive + removable.
- **D2 — A separate append-only file, not `document.session`'s snapshot.** The snapshot
  re-renders (overwrites); the live log grows. WHY: one source of truth per artefact —
  the snapshot stays derivable, the log stays append-only (rule 9).
- **D3 — Best-effort + opt-in.** A session log is notification, never load-bearing; it
  must not fail a verb or pollute bare unit tests. WHY: the frugal floor — secure/correct
  verbs first; logging is the cherry, never the cake.
