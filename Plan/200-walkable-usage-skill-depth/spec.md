---
spec_id: "200"
slug: walkable-usage-skill-depth
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "081"
depends_on: ["081", "152", "147", "146"]
vision_goals: [1, 4]
affects:
  - agency/_skilldoc.py
  - tests/test_walkable_usage_depth.py
---

# Spec 200 — walkable usage-skill depth (adaptive phase budgeting)

## Why

Spec 081 derives a `<cap>-usage` walkable skill per capability (verbs
clustered by role, ≤6 phases, hard confirm gate). The phase clustering
is currently static (by role). For a capability with many verbs, a
fixed ≤6-phase cap either crams or omits. With the Spec 147 Driver, the
derived walk can adapt its phase structure to the actual task the agent
states — pulling only the relevant verbs into the walk — while keeping
the per-phase token budget (Goal 1) and the hard gate.

## Done When

- [ ] **`AdaptiveWalk` typed return** — `AdaptiveWalk = {capability,
      task_hint: str | None, phases: list[Phase], driver_used: bool,
      verb_count_total, verb_count_selected, fallback_reason: str | None}`
      where `Phase = {role, verbs: list[str], instruction, budget_tokens}`.
- [ ] **`<cap>-usage` walk accepts an optional task hint** — the Spec
      147 Driver selects + orders the relevant verbs into ≤6 phases for
      THAT task; degrades to the static role-clustering without
      `[anthropic]`, setting `fallback_reason="anthropic_not_installed"`.
- [ ] **Invariant — per-phase output within budget** (relationship, not
      pinned tokens): for every `phase` returned, `phase.budget_tokens <=
      MAX_PHASE_TOKENS` (configured, default 1500) AND
      `sum(phase.budget_tokens) <= MAX_WALK_TOKENS` (default 6000).
- [ ] **Invariant — adaptive selection is a subset** (relationship):
      `set(selected_verbs) <= set(capability.all_verbs)` AND
      `len(selected_verbs) <= len(all_verbs)` — the Driver never
      hallucinates a verb that doesn't exist in the live registry.
- [ ] **Invariant — confirm gate preserved** (relationship): for every
      walk (adaptive or static), `phases[-1].role == "confirm"` AND the
      confirm phase carries the same hard-gate instruction Spec 081
      ships; a drift fails the invariant.
- [ ] **Invariant — static fallback equality**: when `task_hint is None`
      AND `driver_used=false`, the returned phases equal
      `derive_static_walk(capability)` byte-for-byte (Spec 081
      reproducibility).
- [ ] **Failure mode coverage** — Driver REFUSAL / TIMEOUT / schema
      violation each degrade to the static walk with a typed
      `fallback_reason`, never crash the walk.
- [ ] Test: a task hint produces a task-relevant phase order (mocked
      Driver); static fallback deterministic across two runs; confirm-
      gate invariant asserted over the live capability set.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  capability `develop` has 14 verbs across roles
        [scaffold, edit, test, commit] AND [anthropic] is installed
        AND task_hint = "add a failing test for spec 200"
When:   develop.skill_walk("intent-id", "develop-usage",
                          task_hint=task_hint) runs
Then:   AdaptiveWalk{driver_used:true, verb_count_selected: 4,
        phases: [{role:"test", verbs:["develop.test"], ...},
                 {role:"commit", verbs:["branch.commit_smart"], ...},
                 {role:"confirm", ...}]}
        AND every phase.budget_tokens <= MAX_PHASE_TOKENS
        AND phases[-1].role == "confirm"

Given:  no task hint provided AND [anthropic] not installed
When:   develop.skill_walk(...) runs
Then:   AdaptiveWalk{driver_used:false,
        fallback_reason:"anthropic_not_installed",
        phases == derive_static_walk("develop")}
        AND output bytes are byte-stable across calls (Spec 146)

Given:  Driver TIMEOUT mid-selection
When:   the walk runs
Then:   AdaptiveWalk{driver_used:false, fallback_reason:"timeout",
        phases == derive_static_walk(...)} — never crashes the walk
```

## Failure modes (Nygard)

| Failure | Walk response |
|---|---|
| Driver `REFUSAL` (Spec 147) | fall back to static walk; `fallback_reason="refusal"`; record reflection |
| Driver `RATE_LIMITED` | retry per Spec 147 budget; on exhaustion, static fallback |
| Driver `TIMEOUT` | static fallback with `fallback_reason="timeout"` |
| Driver returns verb not in registry | drop the verb; if selection empty, full static fallback |
| Phase budget exceeded mid-render | trim from the largest phase first; re-emit; never silently truncate |
| Confirm gate omitted by Driver | hard invariant fail; static fallback engaged |
| `task_hint` exceeds input budget | typed `BAD_REQUEST{detail:"hint_too_long"}` |

## Interconnects

- **LLM-driver chain** (147) · **output-budget chain** (146).
- Spec 152 (typed Skill) is the phase type.
- Spec 197 (static-walkable resolve) — adaptive walks honor the same
  precedence rule when an override exists (override > adaptive >
  derived static).
- Spec 201 (TokenCounter API) — phase budgets are counted via the
  best-available backend.
- Spec 149 (derived-doc drift) — adaptive selection that drifts from
  the docstring's role declarations is a drift signal.
- Spec 204 (intent.* wet methods) — shares the `run=True` + Driver-
  optional pattern; same fallback discipline.

## Open questions

1. Adapt phases or just verb selection? **Recommend**: verb selection
   within fixed phase roles v1 (predictable); full phase synthesis
   later behind an `experimental=True` flag once the v1 telemetry
   shows stable budgets.
2. Cache adaptive selections per `(capability, task_hint_hash)`?
   **Recommend**: yes — keyed by content hash; LRU bound on entries;
   honors the Spec 146 prefix discipline by treating the cache key as
   part of the body, not the prefix.
3. How does the agent override the adaptive choice mid-walk?
   **Recommend**: a `revise(phase_index, task_hint_v2)` re-enters the
   walk from that phase; previous phases remain immutable for
   provenance (Spec 017).
