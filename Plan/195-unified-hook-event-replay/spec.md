---
spec_id: "195"
slug: unified-hook-event-replay
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "076"
depends_on: ["076", "021", "156", "176"]
vision_goals: [2, 3]
affects:
  - agency/engine.py
  - agency/capabilities/dogfood/_main.py
  - tests/test_hook_event_replay.py
---

# Spec 195 — unified-hook event replay + boundary-use capture

## Why

Spec 076 ships the unified event-hook (`hooks/dispatch` → `agency hook`
→ `engine.dispatch_hook`; `Event` node + `AGENCY_INTENT` linkage).
Events are recorded but not REPLAYABLE — and Spec 114 Slice 2 (the
deferred BoundaryUse auto-capture on raw Write/Edit/Bash) needs exactly
this hook to record when an agent bypasses a capability verb. This spec
makes the Event stream replayable (provenance reconstruction) and wires
the deferred boundary-use capture.

## Done When

- [ ] **Event replay** — `dogfood.replay_events(intent_id)` reconstructs
      the session's action sequence from `Event` nodes (Goal 2: the
      graph is the record).
- [ ] **Raw-tool boundary-use capture** (Spec 114 Slice 2) — the hook
      records a `BoundaryUse` node when an agent uses raw Write/Edit/Bash
      instead of a capability verb, so the provenance moat sees the
      bypass.
- [ ] **`boundary_use_audit` (Spec 114) reads the captured nodes** —
      "you bypassed the substrate N times; here are the verbs you
      could have used" (feeds the dogfood loop, Spec 150).
- [ ] **Loop-detection events (Spec 156) appear in the replay.**
- [ ] Test: a raw-edit hook records a BoundaryUse; replay reconstructs
      the sequence.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 021 (monitor) + Spec 156 (loop hooks) emit into the stream.
- Spec 176 (sessionstart capture) opens the Intent the events SERVE.
- **dogfood-loop chain** (150): boundary-use bypasses become proposals.

## Open questions

1. Capture every raw tool use or only mutating? **Recommend**: only
   mutating (Write/Edit/Bash) — reads aren't a substrate bypass worth
   flagging.
