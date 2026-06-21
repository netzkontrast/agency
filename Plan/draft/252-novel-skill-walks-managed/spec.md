---
spec_id: "252"
slug: novel-skill-walks-managed
status: draft
state: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "142"
depends_on: ["142", "180", "147", "150", "021", "040", "146", "245", "247"]
vision_goals: [8, 4]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_novel_skill_walks_managed.py
---

# Spec 252 — novel-craft skill walks: Managed-Agent dispatch

## Why

Spec 142 ships six walkable skills (dual-storyform-author /
canon-lock-author / alter-roster-builder / reveal-rule-author /
r-rule-author / chapter-briefing-author). Each is a 4–6 phase walk
suitable for autonomous run via Managed-Agent (claude-api skill).
This adds the dispatch option: a walk runs locally OR as a
Managed-Agent session, events stream back. The harness-in-harness
ladder applied to novel-craft.

## Done When

- [ ] **`skill_walk(name, driver: Literal["local","managed-agent"]=
      "local") -> WalkRun`** — typed return `WalkRun{run_id, name,
      driver, phases: list[PhaseResult{phase_id, status: Literal[
      "pending","running","done","failed"], artefacts: list[ArtefactRef],
      events: list[MonitorEventRef]}], session_id: ManagedSessionId |
      None, parity_hash: str, status: Literal["running","completed",
      "failed"]}`. Local driver runs phases inline; managed driver
      dispatches per Spec 180 + Spec 147 `dispatch_session`; events
      stream as MonitorEvents (Spec 021).
- [ ] **Invariant: artefact parity across drivers** — for the same
      walk + same input, `local.parity_hash == managed.parity_hash`
      where `parity_hash` is computed over the SET of artefact node-
      ids + their typed payloads (NOT timestamps, NOT IDs themselves
      — the SHAPE). Property test asserts parity over the 6 walks.
- [ ] **Invariant: dispatch heuristic decides, doctrine doesn't** —
      Spec 040 11-signal heuristic chooses `local` vs. `managed-agent`
      by default; the `driver=` parameter is an override. Relationship:
      `default_driver == heuristic(signals)`; tests assert the
      heuristic produces stable choices on fixture work-shapes.
- [ ] **Invariant: every walk-minted artefact carries SERVES edge
      back to the dispatching Intent** — provenance moat preserved
      across the harness-in-harness boundary; queryable from the
      parent session.
- [ ] **Invariant: events stream, don't buffer** — for managed dispatch,
      MonitorEvent stream emits per-phase events as they arrive; the
      caller can subscribe and see progress, not just final result.
      Test asserts `>=1` event per phase boundary.
- [ ] **Failure modes**: managed-agent `SESSION_TIMEOUT` mid-walk →
      WalkRun.status="failed", partial artefacts kept, can be resumed
      with `skill_walk(name, resume=run_id)`; Driver `REFUSAL` on a
      phase → phase marks `failed`, walk continues if phase is
      non-blocking (per skill metadata) else aborts; `RATE_LIMITED`
      → retry-with-jitter per Spec 147; parity_hash mismatch between
      drivers → log to Spec 150 (signal: the walk has a non-
      deterministic phase); managed dispatch when `JULES_API_KEY`
      missing → fall back to local with a recorded notice.
- [ ] Test: a walk runs both ways with parity (mocked session); event
      stream emits per phase; resume after fake timeout works.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  the canon-lock-author walk (Spec 142), a 5-phase skill;
        Spec 040 heuristic scores managed-agent for this shape
        (≥4 unfamiliar files, read-only-amplified, S11 local-budget
        not relevant); JULES_API_KEY present
When:   skill_walk("canon-lock-author") dispatches; managed driver
        opens session via Spec 147; phases 1-3 stream MonitorEvents;
        phase 4 hits SESSION_TIMEOUT
Then:   WalkRun.status="failed"; phases 1-3 artefacts persisted with
        SERVES edges to the dispatching Intent; parity_hash computed
        over partial set; resumed via skill_walk("canon-lock-author",
        resume=run_id) re-opens session and continues from phase 4;
        a second run with driver="local" produces identical
        parity_hash on the artefact set
```

## Interconnects

- Spec 180 (research fan-out) is the dispatch pattern.
- **LLM-driver chain** (147) — Managed-Agents bridge; the same Driver
  surface every other spec uses.
- Spec 021 (MonitorEvent) — event streaming substrate.
- Spec 040 (dispatch heuristic) — chooses the driver.
- **Output-budget chain** (146) — per-phase output obeys envelope;
  walk metadata sits in cacheable prefix.
- Spec 245 (sensitivity managed) and Spec 247 (canon approval) — both
  can run AS walks under this dispatch.
- **Dogfood-loop chain** (150) — parity_hash mismatches between
  drivers feed amendment proposals.

## Open questions

1. **Resume granularity.** Resume from last completed phase, or from
   mid-phase checkpoint? **Recommend**: phase boundary only — mid-
   phase resume requires per-skill checkpoint infrastructure not
   yet defined; phase-boundary is uniform and simple.
2. **Parity tolerance.** Strict hash equality, or allow Driver-noise
   in freeform sections? **Recommend**: strict on the artefact SHAPE
   (node-ids + typed payload keys); allow byte-level variance inside
   Driver-authored prose. Test asserts the typed shape parity, not
   the prose parity.
3. **Multi-phase parallelism.** Run independent phases in parallel on
   managed dispatch? **Recommend**: yes when the skill declares phase
   DAG; default sequential. The Spec 142 skills are mostly sequential.
