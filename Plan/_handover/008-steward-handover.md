<!-- agency steward handover — read this first next run -->
# Steward Handover 008 — 2026-06-21

## What shipped this run

**Spec 350 — relevance output filter (Slice 2): `filters:` config registry + three call sites wired.**

Owner directive: *"a generalized configurable Filter class to find the interesting part of an output;
also used in shell and tool-call returns."*

Slice 2 ships the OPT-IN config registry and wires all three call sites listed in the spec.

### Key changes

**`agency/_relevance.py`**
- `_DEFAULT_FILTER_PROFILES: dict[str, dict]` — seeded reference profiles (activities / shell /
  toolcall) with `# AGENCY-DRIFT: filter-profiles` tag. NOT auto-applied (OPT-IN only via config).
- `load_filter_profile(name, path=None) -> dict` — reads `_config._read()["filters"][name]` raw
  (same pattern as Spec 352 `llm.models`). Returns `{}` when absent (fail-open, no breaking change).

**`agency/capabilities/jules/_main.py`**
- `activities(filter=)` now tries a named config profile lookup (`load_filter_profile(filter)`)
  before the keyword-include fallback. Backward-compatible: unknown names still become
  `{"include": [filter]}`.

**`agency/capabilities/shell/_main.py`**
- `capture_filter` applies `load_filter_profile("shell")` to Bash body AFTER structural
  `_apply_filter` (OPT-IN: only runs when user sets `filters.shell:` in config.yaml).

**`agency/engine.py`**
- `_default_hook_handler` PostToolUse path applies `load_filter_profile("toolcall")` to
  `filtered` after `capture_filter` (OPT-IN; fail-open via inner try/except).

**`tests/acceptance/features/relevance.feature`**
- 3 new Slice 2 scenarios (10 total): named config profile drives `jules.activities`;
  `capture_filter` applies shell profile; PostToolUse applies toolcall profile.

**`tests/acceptance/test_relevance.py`**
- Step implementations for Slice 2 scenarios using temp config files + AGENCY_CONFIG env var
  + `_READ_CACHE.clear()` for test isolation.

## Evidence

- RED→GREEN: 10/10 relevance scenarios pass in 1.96 s.
- Pillar suite: relevance + shell + hooks + lifecycle — 75 passed in 194.86 s.
- `scripts/check-drift` → pre-existing spec-id collision drift only (NOT caused by this run).
- `scripts/check-doc-drift --update` → 6 docs re-stamped (engine.py, shell/_main.py, etc. touched).
- `python -m agency.install` → no regen needed (no capability surface changed).
- TODO.md: Spec 350 row updated (Slice 1→Slices 1+2 shipped 2026-06-21).
- `Plan/inprogress/350-relevance-output-filter/spec.md` Followup updated with Slice 2 done/still.

## Lessons learned

1. **OPT-IN is the right default** for config profiles — `_DEFAULT_FILTER_PROFILES` exists for
   docs/reference but returning `{}` when not in config avoids all backward-compat issues.
2. **AGENCY_CONFIG + _READ_CACHE.clear()** is the correct pattern for testing config-dependent code.
3. **toolcalls.rows()** (not `.recent()`) is the ToolcallStore query API.
4. **check-doc-drift --update** is needed after touching engine.py, shell/_main.py, or jules/_main.py
   even for minor additive changes (the source hash changes).

## Candidate investigation notes (from handover 007)

All three candidates from handover 007 were re-evaluated:
1. **Spec 350 Slice 2** — SHIPPED this run. ✓
2. **Spec 350 Slice 3** — PostToolUse call site was included in Slice 2 (engine.py wire).
   Remaining Slice 3 items: graph `FilterProfile` node override + LLM-scored relevance.
3. **Spec 339b** — Still deferred (owner review needed for SessionLifecycle→Lifecycle node-type change).

## Next 3 candidates (ranked)

1. **Spec 350 Slice 3 — graph `FilterProfile` node override**
   Add a `FilterProfile` node type (analogous to Spec 337's structural profiles), allowing
   `shell.define`-style graph overrides for relevance profiles. Low architectural risk, pure
   addition. Acceptance: define a profile via the graph, verify it overrides the config default.

2. **Spec 322 Slice 3 — wire `clarity_gate` as `guided-discovery` discipline's final gate_verb**
   Slice 2 (`clarity_gate` composite verb + override + Gate recording) shipped 2026-06-20.
   Slice 3 is wiring it as `guided-discovery` discipline's final phase. Pure addition in
   `discover/` cluster, no ambiguity.

3. **Spec 339b — `develop._main` lifecycle state-writer migration**
   Migrate `develop._main.py`'s `record_and_serve("SessionLifecycle",…)` to
   `ctx.lifecycle.open(kind="session")` + `move(working)`. The drift-guard exclusion for
   Step.state false-positive still needed. **Needs owner review first** (node-type change:
   SessionLifecycle → Lifecycle; existing data in the graph may differ).

## Pillar gate

- Schema coverage: unchanged (no new schema nodes).
- Drift: pre-existing spec-id collision drift (365-369); no new drift from this run.
- Doc drift: clean (re-stamped 6 docs).
- Install: no diff (no capability surface changed).
- Tests: 10 relevance scenarios green; 75 pillar tests green; no regressions observed.
