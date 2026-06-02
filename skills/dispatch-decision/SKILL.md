---
name: dispatch-decision
description: Use when about to dispatch a task to a subagent (local, Jules, or future MCP-client driver), before invoking `delegate.fan_out` or any other dispatch path — to weigh the 11 token-economics + cache-aware + budget-model signals against staying inline.
allowed-tools:
  - mcp__plugin_agency_agency__execute     # for capability_delegate_dispatch_decision
  - mcp__plugin_agency_agency__search
  - mcp__plugin_agency_agency__get_schema
---

# Dispatch decision (the orchestrator's choice)

## When to use

Before EVERY fan-out, EVERY subagent dispatch, EVERY Jules call.
Substrate verbs (`agency_welcome`, `intent_bootstrap`, etc.) and
read-only graph queries DON'T need this — they're not dispatches.
But for any verb / skill that's about to spawn an isolated context,
the heuristic is binding (CLAUDE.md Rule #3).

## The chain (5 phases — walk `delegate.ontology.skills["dispatch-decision"]`)

```
1. estimate-tokens-and-cache    →  S1, S6, S7, S8, S9, S10, S11
2. estimate-shape               →  S2, S3, S4, S5
3. apply-heuristic              →  {recommendation, driver, signals_fired, rationale}
4. assemble-bash-hints          →  bash_hints (empty when inline)
5. decide(hard gate)            →  inline | dispatch
```

Phase 5 is a hard gate. Don't dispatch until you've walked.

## The 11 signals (at-a-glance)

```
              Dispatch winners              Inline winners
              ─────────────────             ──────────────
work shape:   S1 ≥ 5000 tokens              S1 < 5000
              S2 ≥ 4 unfamiliar files       S2 ≤ 3 known
              S3 repeated exploration       S3 known paths
              S4 ≥ 3 sibling tasks          S4 1–2
              S5 ≥ 15 min wall-clock        S5 < 15
role/safety:  S6 NOT mutating               S6 mutating (no provenance)
              S7 read-only                  S7 writes
hint:         S8 matches signals            S8 conflicts
cost model:   S9 ≤ 0.3 overlap              S9 ≥ 0.7 (re-load tax)
              S10 ≤ 0.3 cache cold          S10 ≥ 0.6 cache hot (10% cost)
budget:       S11 False (Jules)             (S11 True relaxes nothing)
              ↓                              ↓
          local OR jules                   inline
```

Two **disqualifiers** ALWAYS fire BEFORE positive scoring:
1. `mutates=True` + verb not effect-with-provenance → inline.
2. (Only when `local_budget_relevant=True`) high overlap + low return
   OR hot cache + short duration → inline.

Then: any positive signal → dispatch (driver picked by §"Driver matrix"
in [`references/driver-matrix.md`](references/driver-matrix.md)); no
positive signal → inline.

## How to call

```python
r = await call_tool('capability_delegate_dispatch_decision', {
    # work-shape (S2-S5)
    'file_count': 5,
    'exploration_needed': True,
    'parallelism': 3,
    'est_duration_min': 12,
    # new return-token + role + cache signals (S1, S6-S11)
    'expected_return_tokens': 6000,
    'mutates': False,
    'read_only': True,
    'driver_hint': 'local',           # tie-breaker, not override
    'context_overlap': 0.2,           # 0..1; parent already-loaded fraction
    'cache_warmth': 0.4,              # 0..1; parent prompt-cache hit ratio
    'local_budget_relevant': True,    # False → Jules path
})
# r → {recommendation, driver, rationale, token_cost_estimate,
#      local_budget_token_estimate, signals_fired}
```

## When the answer is `dispatch`

Use **`local`** for read-only fan-outs and context-isolation (3+
parallel siblings). Use **`jules`** for heavy compute + async-tolerable
(≥45min or `local_budget_relevant=False`). The driver field tells you
which capability to call next — `delegate.fan_out`/`subagent.spawn` for
local, `jules.dispatch` for Jules.

## When the answer is `inline`

Don't dispatch. Phase 4 returns empty `bash_hints`. The rationale
explains which signal pinned the decision.

## References (the depth)

- [`references/heuristics.md`](references/heuristics.md) — the eleven
  signals + disqualifiers + the full pseudocode algorithm.
- [`references/driver-matrix.md`](references/driver-matrix.md) — when
  each of the 4 drivers wins; per-driver cost models.
- [`references/anti-patterns.md`](references/anti-patterns.md) — five
  don'ts (loop-body dispatch, known-path lookup, etc.).
- [`references/cache-and-budget-model.md`](references/cache-and-budget-model.md)
  — context-overlap, Anthropic prompt-cache pricing (5-min TTL, 10%
  cached input), Jules's separate budget.

## Doctrine

This skill IS CLAUDE.md Rule #3 ("Decide before dispatching"). The
heuristic is binding — every dispatch path consults
`delegate.dispatch_decision` first. The skill's hard gate (Phase 5)
makes that machine-enforced when walked via `skill.walk`.
