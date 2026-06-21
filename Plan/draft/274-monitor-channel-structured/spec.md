---
spec_id: "274"
slug: monitor-channel-structured
status: draft
state: draft
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

- [ ] **`MonitorEvent` graph node** with typed shape:
      `{event_id: ULID, intent_id: str, driver: str | None,
       session_id: str | None, kind: Literal[<enum>], ts: iso8601,
       payload: dict}` + `SERVES` edge to the originating Intent +
      optional `EMITTED_BY` edge to the driver session node.
- [ ] **Background ingest** drains the SLOG into graph nodes — bounded
      worker (queue size cap), idempotent on `event_id` (re-ingest of a
      duplicate is a no-op, not an error). Worker checkpoints last
      ingested offset per SLOG file to survive restart.
- [ ] **`analyze.graph_query` (Spec 203)** answers monitor questions in
      one call (`"silent_fail in last 1h"`, `"loop_detect for intent
      X"`). The query surface returns typed `MonitorEvent` shapes, not
      raw rows.
- [ ] **The SLOG stays the fast-path append** (Spec 021 doctrine) —
      ingest is async; orchestrator never blocks on graph write; SLOG
      append latency unchanged by ingest presence.
- [ ] **Output budget honored** (Spec 146) on monitor queries — a query
      returning >budget bytes paginates with a stable prefix.
- [ ] **Invariants** (CLAUDE.md rule 8):
      - For every event line in the SLOG with `event_id=e`,
        eventually `exists(MonitorEvent where event_id=e)` in the
        graph (eventual consistency; bounded by worker lag).
      - `count(distinct MonitorEvent.event_id) ==
        count(distinct SLOG.event_id)` post-ingest (no drops, no
        duplicates).
      - SLOG append p99 latency with ingest running ≤ p99 latency with
        ingest disabled × 1.1 (≤10% overhead).
      - `set(MonitorEvent.kind) == set(spec_021_event_kinds) ∪
        set(spec_271_event_kinds)` — the kind enum is open-set via
        capability extension, not a frozen literal.
- [ ] **Failure modes table** — see below.
- [ ] Test: emit→ingest→query round-trip; SLOG rotation works
      independent of ingest; duplicate event_id ingest is idempotent;
      worker restart resumes from checkpoint; query honors output
      budget.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  Jules verb (Spec 012) emits a silent_fail_detected SLOG line
        with event_id=01HQK... and intent_id=int_abc
When:   the background ingest worker drains the SLOG
Then:   a MonitorEvent node lands in the graph with the typed shape;
        SERVES edge connects to Intent int_abc; analyze.graph_query
        "silent_fail in last 1h for intent int_abc" returns it

Given:  worker crashes mid-ingest after processing offset 4096 of a
        1MB SLOG segment
When:   worker restarts
Then:   resumes from checkpointed offset 4096; events 0..4095 are NOT
        re-ingested (idempotency via event_id); events 4096..EOF
        ingest; invariant count-equality holds

Given:  a postmortem query "every silent_fail across all drivers in
        the last 24h" against a graph with 50k MonitorEvents
When:   analyze.graph_query runs
Then:   typed MonitorEvent shapes return; Spec 146 output budget caps
        the return at the page size; a next_cursor in the response
        lets the orchestrator fetch the next page without re-loading
        the prefix
```

## Failure modes

| # | Failure | Detection | Response |
|---|---|---|---|
| F1 | Ingest worker falls behind (queue saturated) | Queue depth metric | Backpressure SLOG writers? NO — SLOG must stay non-blocking. Instead drop oldest queued + emit `ingest_lag_detected` MonitorEvent (graph remains the slow path; SLOG remains the truth) |
| F2 | SLOG line malformed (parse error) | Worker JSON decode | Skip line; emit `slog_parse_error` MonitorEvent with byte offset; do NOT crash worker |
| F3 | Duplicate event_id arrives (re-ingest after restart) | Graph uniqueness constraint on event_id | No-op; idempotency invariant preserved |
| F4 | Graph write fails (DB locked, schema mismatch) | Transaction error | Retry with backoff; on persistent failure log to a fallback `ingest_dlq.jsonl` + emit `ingest_failure_persistent` |
| F5 | Query payload exceeds Spec 146 output budget | Pre-serialize size check | Paginate with stable prefix + next_cursor; never silently truncate |
| F6 | Open-set kind enum drift (capability adds a kind not in registered set) | Spec 054 drift gate on `MonitorEvent.kind` | Gate fails CI with the new kind + the file where it's emitted but not registered |

## Interconnects

- Spec 021 (parent) — atomic-append SLOG fast-path stays the truth.
- Spec 195 (event replay) is the sibling discipline for hook events;
  shares the ingest worker pattern.
- Spec 203 (graph query) is the query surface; typed return shape.
- Spec 146 (output budget) caps query payloads.
- Spec 271 (Jules/MA bridge) emits `driver`-tagged events into this
  same stream — kind enum is open-set via capability extension.
- Spec 275 (Jules amendment loop) consumes the queryable monitor for
  recurring-pattern mining.
- Spec 273 (DB migrations) records `MigrationApplied` here.
- Spec 276 (doctor) reads ingest-lag + DLQ depth as readiness signals.
- **Provenance** (Goal 2) extended to monitor events; **agent-uniform
  Lifecycle** (Goal 3) — one event stream regardless of driver.

## Open questions

1. **Ingest cadence.** Continuous worker, or periodic flush?
   **Recommend**: continuous worker with backoff — periodic flush
   invites a "missing the last 30s" gap in postmortems; continuous
   keeps the graph within seconds of SLOG truth.
2. **DLQ retention.** How long do `ingest_dlq.jsonl` lines stay?
   **Recommend**: rotate at 1 MB (mirroring SLOG); keep last 7 days
   on disk; a stuck DLQ is a doctor-visible alert (Spec 276).
3. **Re-ingest of historical SLOG.** Should `agency_doctor` offer a
   "re-ingest from offset 0" command for upgraded graphs?
   **Recommend**: yes — gated behind `--force` since it's slow; the
   idempotency invariant makes it safe; useful after schema
   migrations that add fields.
