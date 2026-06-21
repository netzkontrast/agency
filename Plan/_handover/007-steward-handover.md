<!-- agency steward handover — read this first next run -->
# Steward Handover 007 — 2026-06-20

## What shipped this run

**Spec 350 — relevance output filter (Slice 1).**

Owner directive: *"a generalized configurable Filter class to find the interesting
part of any output — for starters only show activities of interest; also used in
shell and tool-call returns."*

Slice 1 ships the pure helper + two call sites (shell `_apply_filter` + jules
`activities`). The `filters:` config registry and the PostToolUse call site are
Slice 2.

### Key changes

**`agency/_relevance.py`** (NEW)
- `relevance_filter(text, profile) → {kept, matched, elided, locator}` — pure,
  content-aware include/exclude/context/budget filter over lines of text.
- `include` patterns: any-match keeps the line. Empty = keep all (then apply exclude).
- `exclude` wins over include.
- `context` — neighbour lines around each match.
- `budget` — caps the WIRE return, never the stored capture (CLAUDE.md #9).
- `locator` — `sha16:<sha256[:16]>` always present (never silent).
- Fail-open: bad regex silently skipped; bad profile → all lines kept, `elided=0`.

**`agency/capabilities/shell/_main.py`**
- `_apply_filter` gains a `relevance:<JSON profile>` strategy branch.
- Dispatches to `relevance_filter`; fail-open on bad profile JSON.

**`agency/capabilities/jules/_main.py`**
- `activities(...)` gains `filter: str = ""` parameter.
- When `filter` is set and `full=False`: runs `relevance_filter` on
  `f"{kind} {summary}"` for each activity, keeps only matched ones, adds
  `filter_applied` key to result.
- `full=True` bypasses filter entirely (existing raw escape hatch preserved).

**`tests/acceptance/features/relevance.feature`** (NEW)
- 7 Gherkin scenarios: pure helper (3) + `_apply_filter` integration (1) +
  `jules.activities` filter (1) + `jules.activities full=True` bypass (1) +
  exclude-wins (1).

**`tests/acceptance/test_relevance.py`** (NEW)
- Full step implementations. `_StubJulesBackend` returns fixed activities
  (agentMessaged + heartbeat). Uses `Engine(jules_client=stub)` → `registry.invoke`.

## Evidence

- RED→GREEN: 7/7 scenarios pass in 1.44 s.
- `scripts/check-drift` → NO DRIFT.
- `scripts/check-doc-drift` → NO DOC DRIFT.
- `python -m agency.install` → install clean (no regen needed).
- TODO.md: Spec 350 row updated (Drafted → Partial; Partially-implemented count 0→1).
- `Plan/inprogress/350-relevance-output-filter/spec.md` Followup updated with Slice 1 done/still.

## Candidate investigation notes

The handover 006 listed three candidates. Investigation results:

1. **Spec 153 `--fix-baseline` auto-trim** — MOOT. `Plan/_planning/schema-coverage-baseline.txt`
   is all-comments (coverage already 1.0). No trim to automate.
2. **`scripts/check-drift` dormant-schemas gate** — ALREADY DONE. Section 6 in
   `scripts/check-drift` already ships the `dormant schemas: none` gate.
3. **Spec 339b lifecycle state-writer migration** — DEFERRED. Changes `develop/_main.py`'s
   `SessionLifecycle` node type → `Lifecycle`, extra fields, architecturally significant.
   The drift-guard exclusion for `develop/_main.py` would still be needed (Step.state
   false-positive). Needs owner review before a steward attempt.

Chose **Spec 350 Slice 1** as the clearly-scoped, zero-ambiguity increment.

## Next 3 candidates (ranked)

1. **Spec 350 Slice 2 — `filters:` config registry**
   Add a `filters:` section to `.agency/config.yaml` (read via `_config._read()`,
   same pattern as Spec 352's `load_registry_from_config`). Let users override
   `include`/`exclude`/`context`/`budget` per-tool without code changes. No
   architectural ambiguity; pure addition on the shipped helper. Acceptance:
   load config, assert override wins over the code default.

2. **Spec 350 Slice 3 — PostToolUse call site**
   Wire `relevance_filter` into the PostToolUse capture path (the third call site
   after shell + jules). The `_default_hook_handler` in `engine.py` routes PostToolUse
   through `capture_filter`; add a `relevance:` profile lookup there. Needs Slice 2
   (config registry) to be meaningful, so do Slice 2 first.

3. **Spec 339b — `develop._main` lifecycle state-writer migration**
   Migrate `develop._main.py`'s `record_and_serve("SessionLifecycle",…)` on line 1147
   to `ctx.lifecycle.open(kind="session", parameterization="…")` + `move(working)`.
   The drift-guard exclusion for the Step.state false-positive still needed. Check
   with owner first given the node-type change (SessionLifecycle→Lifecycle).

## Pillar gate

- Schema coverage: 1.0 (unchanged).
- Drift: clean (check-drift NO DRIFT).
- Doc drift: clean.
- Install: no diff.
- Tests: 7 new scenarios green; no regressions observed.
