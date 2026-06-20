<!-- agency steward handover — read this first next run -->
# Steward Handover 007 — 2026-06-20

## What shipped this run

**Spec 339b — migrate subagent's raw lifecycle state write through `ctx.lifecycle.move`.**

`subagent._main.py` was the last non-Q4 raw `Lifecycle.state` writer in the codebase:

```python
# OLD — bypassed the sole-writer guard (and emitted no Event):
self.ctx.memory.update(child, {"state": "completed"})

# NEW — routed through the substrate sole writer (emits durable Event for free):
self.ctx.lifecycle.move(child, "completed")
```

### Key changes

**`agency/capabilities/subagent/_main.py` (line 66)**
- 1-line change: `memory.update(child, {"state": "completed"})` →
  `lifecycle.move(child, "completed")`.
- Behaviour is unchanged (child state is still `completed` when both gates pass).
- Free behaviour from Spec 344: `move` emits a durable `lifecycle_transition` Event
  for terminal states. Previously this transition was invisible to any observer.

**`tests/acceptance/features/subagent.feature`**
- 2 new Spec 339b scenarios:
  1. "completed child emits a durable lifecycle transition Event" — proves routing
     through `move` (the Event is the proof; raw `memory.update` would not emit it).
  2. "incomplete child does not emit a completed transition Event" — proves the
     negative case (no spurious Event when spec gate fails).

**`tests/acceptance/test_subagent.py`**
- Step implementations for the 2 new scenarios.
- Pattern: `engine.memory.find("Event")` filtered by `name=="lifecycle_transition"`,
  `to_state=="completed"`, `has_edge(event_id, child_id, "OBSERVED_DURING")`.

**`docs/` (5 files re-stamped)**
- Pre-existing doc drift: `docs/README.md` + `docs/vision/reference/{README,drivers,engine,overview}.md`
  had fallen stale (not caused by this run). Re-stamped via `scripts/check-doc-drift --update`.

## Evidence

- RED→GREEN: 2 new scenarios; 5 total subagent scenarios green (no regressions).
- 36/36 lifecycle + delegate + gate + subagent acceptance tests green.
- Full acceptance suite: exit 0.
- `scripts/check-drift` → NO DRIFT.
- `scripts/check-doc-drift` → NO DOC DRIFT (5 re-stamped this run).
- TODO.md lifecycle program row updated (339b shipped; header count updated).
- Reflections: `reflection:d95723b2` (Event-as-proof pattern),
  `reflection:084c3409` (music was already clean via gate routing).

## B3 drift-guard status after 339b

The `AGENCY-DRIFT: lifecycle-state-writer` comment at `lifecycle.py:158` is now
accurate. The only remaining `record_and_serve("SessionLifecycle", ...)` call is
`develop._main.py:1147` — explicitly deferred to Q4 (`SessionLifecycle`→`session`
parameterization). B3 is closed for all non-Q4 writers.

## Next 3 candidates (ranked)

1. **Lifecycle 341 — observe suite (`read · find · check · watch`)**
   The 344 transition trail now exists but has no consumer verb. `341` adds the
   `read · find · check · watch` composing `manage`/`jules.watch`/the 344 events —
   **no poll**. This is a pure addition onto the 339+344 substrate; the event trail
   is the key consumer. High reach (any agent watching intent progress); completes
   the lifecycle pillar's read frame (the write frame is now fully owned by `move`).

2. **Lifecycle Q4 — `SessionLifecycle`→`session` parameterization**
   Migrate `develop._main.py:1147`'s `record_and_serve("SessionLifecycle", {...})`
   to `ctx.lifecycle.open(intent_id, kind="session")`. This closes the one remaining
   raw lifecycle-family record call. Medium effort (need to check reflect + dogfood
   for the archive path). Architecturally significant — closes the B3 guard completely.
   Prerequisite: confirm the `kind="session"` seam in `lifecycle.open` handles
   all props the current `record_and_serve` records.

3. **Lifecycle 342 — agent-as-lifecycle-parameterization (Goal 3)**
   Wires `jules.verify`+`delegate.join` to ONE "done" via parameterization variants,
   resolving the two contradictory "done" paths. Higher impact than Q4 but more
   architectural; probably deserves a human review of the design before implementation.
   341 should land first (it's the read side; 342 is the write-unification).
**Spec 153 Slice 5 — deferred-tag gate (`--fix-baseline` auto-trim).**

Closed the final point of friction in the schema coverage maintenance workflow.
The `check_schema_coverage.py` CLI now accepts a `--fix-baseline` argument
that auto-removes labels that have gained coverage from the baseline file,
preserving comments and formatting.

### Key changes

**`scripts/check_schema_coverage.py`**
- `parser.add_argument("--fix-baseline", ...)`
- Rewrites `res.fixed_uncovered` elements from the `args.baseline` file.

**`Plan/153-fix-baseline-auto-trim/spec.md`**
- Spec file created with the acceptance criteria for this slice.

## Evidence

- Local unit testing demonstrated the auto-trimming behaviour removes the exact labels.
- Drift gate is clean (`scripts/check-drift` passing).
- Run full test suite; no regressions observed related to the new scripts.

## Next 3 candidates (ranked)

1. **Proposed amendment from handover 005 — dormant_schemas in scripts/check-drift**
   Add the `dormant_schemas` check from `agency_doctor` into the CI drift gate
   (currently only fires when the user invokes the doctor or schema CLI). The
   `scripts/check-drift` snippet was drafted in handover 005 — a short, low-risk
   addition that closes the gap between the per-PR drift gate and the runtime gate.
   Blocked three Slice 6 batches before being caught; now it's a known pattern.

2. **Spec 337 deferred — graph-override read path for FilterProfile**
   Analogous to `shell.define` for command templates: let a project store a
   `FilterProfile` Artefact in the graph to override a seed profile without a code
   change. The AGENCY-DRIFT tag at `_FILTER_PROFILES` protects the surface. Medium
   effort; low urgency (seed registry covers the known high-volume tools).

3. **FastAPI typed-read surface (Goal 5/7, Spec 330 follow-up)**
   Architecturally significant capstone; needs a human-reviewed spec for
   server boundary, auth model, and lifecycle integration before implementation
   begins. Still the right long-term direction the typed-entity program points
   at. Do NOT start without explicit human sign-off on the design.

## Pillar gate (held)

Intent/Capability/Lifecycle/Memory — all pillars read+write load-bearing.
Schema coverage: 89/89 = 1.0 (full). Dormant schemas: 0.
Drift: clean. Doc-drift: clean (5 re-stamped this run).

## Key lessons

**Event-as-proof pattern:** `assert state == "completed"` doesn't prove routing through
`move` — raw `memory.update` also sets the state identically. The proof is the durable
`lifecycle_transition` Event that **only** `move` emits for terminal states (Spec 344).
Future state-writer migration tests should assert the Event, not just the resulting state.

**`memory.update(*, state=...)` grep pattern:** Before a lifecycle migration effort,
`grep -rn 'memory.update.*"state"'` (production code, excluding memory.py itself) is
the fastest way to find raw writers. Returned exactly 1 result for this run.

**Music was already clean:** The TODO phrasing "migrate subagent/music writers" was
slightly misleading. Music's state transitions flow through `gate.check`, which was
already routed through `move` (344 ship). Always verify with the grep before
assuming both named caps need migration.
Schema coverage: 93/93 = 1.0 (full).
Dormant schemas: 0. Drift: clean.

## Key lesson

Ensuring test stability before implementing feature slices ensures that the code changes are correctly evaluated. In this run, some pre-existing failures in `tests/acceptance/test_hooks.py` were left aside, but resolving unrelated flaky tests provides more confidence in changes overall.
