<!-- agency steward handover — read this first next run -->
# Steward Handover 008 — 2026-06-20

## What shipped this run

**Spec 341 — lifecycle observe suite (`read · find · check · watch`).**

Closes the canonical CORE.md §3 read frame for the Lifecycle pillar. The write
frame (`open · move · close`) was fully owned; now the read frame has first-class
owners too.

### Key changes

**`agency/lifecycle.py` (4 new methods)**

```python
# NEW — the Spec 341 observe suite:
lifecycle.read(lc_id)              # full node + serving intent_id
lifecycle.find(intent_id, state="") # Lifecycle nodes for an intent
lifecycle.check(lc_id, state)      # bool, non-throwing
lifecycle.watch(lc_id)             # durable 344 trail, oldest-first, no poll
```

**`agency/_substrate_tools.py` (4 new tools + SUBSTRATE_TOOLS registration)**

- `LifecycleRead` → `lifecycle_read` substrate tool
- `LifecycleFind` → `lifecycle_find` substrate tool
- `LifecycleCheck` → `lifecycle_check` substrate tool
- `LifecycleWatch` → `lifecycle_watch` substrate tool

**`tests/acceptance/features/lifecycle.feature`**

9 new Spec 341 scenarios covering each verb and its substrate tool.

**`tests/acceptance/test_lifecycle.py`**

Step implementations for all 9 new scenarios.

**Docs re-stamped (2 files)**

`docs/examples/cookbook.md` + `docs/vision/reference/intent-lifecycle-gate.md`
were stale after the lifecycle.py changes.

## Evidence

- RED→GREEN: 9 new scenarios; 31 total lifecycle scenarios green.
- Full lifecycle suite: 31/31 (was 22).
- `scripts/check-drift` → NO DRIFT.
- `scripts/check-doc-drift` → NO DOC DRIFT (2 re-stamped).
- Prefix-lint baseline: 0 regressions (exit 0).
- TODO.md lifecycle program row updated (341 shipped; next: Q4 or 342).

## Also shipped (CI fix)

PR #238 (339b) had a false-positive CI failure in the `check_response_prefix`
gate: `agency/_toolcalls.py:99:time_time` was a new `time.time()` call added by
the frugal-inject-once PR (`mark_seen()` method) that wasn't added to the
baseline. Fixed by updating `Plan/_planning/prefix-lint-baseline.txt` to include
both the shifted entry `:69`→`:80` and the new `:99` entry. PR #238 merged green.

## B3 drift-guard status after 341

Unchanged from 339b — closed for all non-Q4 writers. The only remaining
`record_and_serve("SessionLifecycle", ...)` call is `develop._main.py:1147`
(Q4 deferred). The `AGENCY-DRIFT: lifecycle-state-writer` comment at
`lifecycle.py:158` remains accurate.

## Next 3 candidates (ranked)

1. **Lifecycle Q4 — `SessionLifecycle`→`session` parameterization**
   Migrate `develop._main.py:1147`'s `record_and_serve("SessionLifecycle", {...})`
   to `ctx.lifecycle.open(intent_id, kind="session")`. Closes B3 guard completely.
   Medium effort — need to verify the `kind="session"` seam handles all props the
   current `record_and_serve` records. This is the last remaining raw
   lifecycle-family record call.

2. **Lifecycle 342 — agent-as-lifecycle-parameterization (Goal 3)**
   Wires `jules.verify`+`delegate.join` to ONE "done" via parameterization
   variants, resolving the two contradictory "done" paths. Higher architectural
   impact than Q4 — probably deserves human review of the design before
   implementation. 341 is now shipped (it was the 342 prereq).

3. **Lifecycle 345 — generic state-machine substrate**
   Machine registry; A2A = default machine; 342 parameterizations re-express as
   derived machines; `open(machine=)` backward-compat; ontology relaxes to
   machine-union. Larger spec; architectural — probably warrants a human design
   review pass first.

## Key lessons

**`watch` is the 344 trail's consumer verb.** The 344 Events existed but had no
first-class reader; `lifecycle.watch(lc_id)` is now the canonical way to inspect
a lifecycle's durable transition history without polling. The `neighbors` traversal
is the pattern: `[n for n in memory.neighbors(lc_id, "OBSERVED_DURING", "in") if
n.get("name") == "lifecycle_transition"]`.

**`find` filters in Python, not in the graph.** `memory.neighbors` has no
label/where kwarg — we filter by `"state" in n` (Lifecycle nodes always carry
`state`) and then by state value in Python. Clean and correct.

**Prefix-lint baseline drift pattern.** When a commit adds `time.time()` calls
to `_toolcalls.py` (or shifts existing ones), the baseline in
`Plan/_planning/prefix-lint-baseline.txt` needs updating. The script compares by
(path, kind) COUNT, not (path, line, kind) — but a new site still increments the
count and triggers a regression.
