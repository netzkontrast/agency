---
spec_id: "274"
slug: monitor-channel-structured
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "021"
depends_on: ["021", "203", "195", "146"]
vision_goals: [2, 3]
affects:
  - agency/_monitor.py
  - tests/test_monitor_structured.py
---

# Spec 274 — monitor channel: structured + queryable

## Why

Spec 021 ships the JSONL append SLOG (1 MB rotation, 4096-byte atomic-
append budget). Today the log is OPAQUE — a postmortem reads JSON lines
by hand. Spec 195 (event replay) builds Event nodes from hook dispatch;
the monitor channel should land the same way: each emitted MonitorEvent
is a graph node, queryable via Spec 203 — "every silent-fail in the
last hour", "every loop-detect for intent X". The SLOG stays as the
fast-path append; periodic ingestion converts to graph for query.

## Done When

- [ ] **`MonitorEvent` graph node** + SERVES edge to the originating
      Intent.
- [ ] **Background ingest** drains the SLOG into graph nodes (bounded
      worker, idempotent on event-id).
- [ ] **`analyze.graph_query` (Spec 203)** answers monitor questions in
      one call.
- [ ] **The SLOG stays the fast-path append** (Spec 021 doctrine) —
      ingest is async; orchestrator never blocks on graph write.
- [ ] **Output budget honored** (Spec 146) on monitor queries.
- [ ] Test: emit→ingest→query round-trip; SLOG rotation works
      independent of ingest.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 195 (event replay) is the sibling discipline for hook events.
- Spec 203 (graph query) is the query surface.
- **Provenance** (Goal 2) extended to monitor events.
