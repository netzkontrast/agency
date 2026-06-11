---
spec_id: "271"
slug: jules-managed-agents-bridge
status: draft
last_updated: 2026-06-11
owner: "@agency"
enhances: "012"
depends_on: ["012", "147", "180", "021"]
vision_goals: [3, 8]
affects:
  - agency/capabilities/jules/_main.py
  - agency/capabilities/delegate/_main.py
  - tests/test_jules_managed_bridge.py
---

# Spec 271 — Jules ↔ Managed-Agents bridge

## Why

Spec 012 ships the full Jules v1alpha lifecycle (dispatch + watcher +
recovery). Per the `claude-api` skill, Managed-Agents is Anthropic's
in-house remote-agent surface — same shape as Jules (persisted agent,
session-based, event streams, `COMPLETED ≠ done`). The agent-uniform
Lifecycle promise (Goal 3) means both should plug into the same
substrate; the harness-in-harness ladder (Goal 8) means an agency walk
can dispatch to EITHER Jules or a Managed Agent.

The CORE doctrine `COMPLETED ≠ done` (CORE.md:44, CORE.md:184) is the
LOAD-BEARING anchor: a remote driver that reports `state=completed`
without a verifiable artefact (Jules: branch on origin; MA: session
output committed to graph) is **silently failing**. Both drivers MUST
share the same verify discipline.

## Done When

- [ ] **`RemoteDriver` protocol** (`agency/_remote.py`) defines the
      shared shape: `dispatch(spec) -> SessionId`, `poll(sid) ->
      DriverState`, `verify(sid) -> VerifiedArtefact | NotDone`,
      `recover(sid) -> RecoveryAction`. `DriverState` is a typed enum
      `{SUBMITTED, WORKING, INPUT_REQUIRED, COMPLETED, FAILED, CANCELED}`
      aligned with A2A (CORE.md:41). `VerifiedArtefact = {kind:
      Literal["branch","commit","graph_node"], ref: str, sha: str}`.
- [ ] **`COMPLETED ≠ done` discipline shared** — neither driver may emit
      a Lifecycle `done` transition until `verify()` returns a
      `VerifiedArtefact`. Jules verify = `state==COMPLETED AND branch
      exists on origin` (CORE.md:184 lesson). MA verify = `session
      output recorded as graph Artefact node with PRODUCES edge`. A
      `COMPLETED`-without-verified state is a `silent_fail_detected`
      MonitorEvent (Spec 021/274), not a `done` transition.
- [ ] **`delegate.dispatch_remote(driver=...)`** routes via the Spec 040
      11-signal heuristic. `driver ∈ {"auto","jules","managed_agent"}`.
      `auto` consults Spec 040; explicit overrides skip the heuristic
      but still record the decision as a Reflection (per Spec 040
      provenance rule).
- [ ] **Events normalize as MonitorEvents** (Spec 021/274) regardless of
      driver — one stream, one watcher. Event schema:
      `{event_id, intent_id, driver, session_id, kind: Literal[
      "dispatched","state_changed","input_required","completed",
      "verified","silent_fail_detected","recovery_started","recovered"],
      ts, payload}`. The `driver` field is the ONLY shape difference.
- [ ] **One watcher (Spec 012) handles both** — `_jules_watcher` renames
      to `_remote_watcher`, dispatches on `event.driver`. Recovery flows
      are driver-specific but invoked through the same hook.
- [ ] **Failure modes table** — see below.
- [ ] **Invariants** (CLAUDE.md rule 8 — relationships, not pinned counts):
      - `count(COMPLETED transitions) ≥ count(done transitions)` always
        — `done` is a strict subset gated by verify.
      - For every Jules and MA session,
        `len(MonitorEvents.filter(driver=d).distinct(kind)) ⊆
         len(MonitorEvents.distinct(kind))` — kind enum is shared.
      - `verify()` is total over `DriverState.COMPLETED` — no
        completed session may live without a `VerifiedArtefact` OR a
        `silent_fail_detected` event within the watcher's
        `verify_window_s` (Spec 022 default 300s).
- [ ] **Test:** a dispatch routes to MA when 11-signal favors it; Jules
      otherwise; both record matching provenance shapes; a mocked
      `COMPLETED` without a branch/Artefact emits `silent_fail_detected`,
      not `done`.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  intent.purpose = "refactor agency/_db.py to use migrations" and
        Spec 040 11-signal scores S6=0 (read-only), S5=1 (>15min),
        S9=0.3 (low overlap), local_budget_relevant=False (S11)
When:   delegate.dispatch_remote(driver="auto", spec=...) runs
Then:   heuristic routes to jules (S11 → Jules path); a `dispatched`
        MonitorEvent emits with driver="jules"; watcher polls; on
        Jules-reported state=completed the watcher calls verify();
        verify finds branch jules/refactor-db on origin → emits
        `verified` then transitions Lifecycle to `done`

Given:  same intent but Jules reports state=completed with NO branch
        on origin within verify_window_s=300
When:   verify() returns NotDone
Then:   emit silent_fail_detected MonitorEvent (NOT done); recovery
        flow triggers per Spec 012; the COMPLETED-but-unpushed case
        from CORE.md:184 is caught — never silently treated as done

Given:  driver="managed_agent" explicit override on a write-mutating
        spec (S6=1 disqualifier on auto)
When:   dispatch_remote runs
Then:   dispatch proceeds (explicit override) BUT the override is
        recorded as a Reflection naming the bypassed disqualifier; on
        MA state=completed verify() requires a graph Artefact with
        PRODUCES edge before `done`
```

## Failure modes

| # | Failure | Detection | Response |
|---|---|---|---|
| F1 | Jules reports COMPLETED, no branch on origin | `verify()` returns NotDone within `verify_window_s` | Emit `silent_fail_detected`; trigger recovery (Spec 012); never emit `done` |
| F2 | MA reports completed, no graph Artefact PRODUCES edge | Same gate against the graph | Same response — driver-symmetric |
| F3 | Driver API unreachable (network, 5xx) | Poll exception with retry exhaustion | Transition to `FAILED`; emit `state_changed`; surface to orchestrator |
| F4 | Mixed driver event stream lost ordering | `event_id` monotonic per session check fails | Ingest pipeline (Spec 274) deduplicates by event_id; alert via `analyze.graph_query` |
| F5 | Explicit `driver=` override bypasses S6 disqualifier (mutating) | Pre-dispatch heuristic comparison | Allow but record Reflection naming the bypass; show in `dispatch_decision` audit |
| F6 | `verify_window_s` elapses with no terminal state | Watcher timer | Emit `silent_fail_detected` with `reason="verify_timeout"`; do NOT auto-cancel — escalate to orchestrator |

## Interconnects

- Spec 012 (Jules lifecycle) is the parent — this generalizes its
  watcher.
- Spec 147 (AnthropicDriver) provides the MA session API surface.
- Spec 180 (research fan-out) is the first verb-level consumer of the
  unified `dispatch_remote`.
- Spec 040 (dispatch-decision) governs the choice; Spec 277 refines
  borderline cases via LLM.
- Spec 021 / Spec 274 (monitor channel) — MonitorEvent stream is the
  shared substrate.
- Spec 022 / Spec 275 (Jules-monitor amendment loop) consumes the
  unified stream — driver-agnostic dogfooding.
- Spec 276 (doctor managed-aware) reports `dispatch_remote` readiness
  per driver.
- **Agent-uniform Lifecycle** (Goal 3) closure; **harness-in-harness**
  (Goal 8) extension.

## Open questions

1. **Symmetric vs asymmetric verify.** Should Jules and MA share an
   identical `verify()` predicate, or driver-specific? **Recommend**:
   identical *protocol* (`VerifiedArtefact | NotDone`), driver-specific
   *predicate* — Jules checks origin branches; MA checks graph
   Artefacts. The discipline is uniform; the evidence shape differs.
2. **Watcher cardinality.** One watcher process, or one per driver?
   **Recommend**: one process, multiplexed on `event.driver` — keeps
   the SLOG single-writer (Spec 021 atomic-append invariant) and
   simplifies the recovery hook.
3. **Recovery escalation timing.** After what window does
   `silent_fail_detected` escalate to a human ping? **Recommend**:
   `verify_window_s * 3` (default 900s) — three failed verify cycles
   is "stuck", not "slow".
