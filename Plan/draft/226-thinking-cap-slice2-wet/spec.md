---
spec_id: "226"
slug: thinking-cap-slice2-wet
status: draft
state: draft
last_updated: 2026-06-11
owner: "@agency"
enhances: "110"
depends_on: ["110", "204", "147", "150", "146", "111", "149", "225", "227", "229"]
vision_goals: [4, 6]
affects:
  - agency/capabilities/thinking/_main.py
  - tests/test_thinking_cap_slice2.py
---

# Spec 226 — thinking capability Slice 2 (remaining methods + wet)

## Why

Spec 110 (thinking-capability) is Partial — Slice 1 shipped 11 verbs;
Slice 2 names "4 remaining methods (pre_commitment, bayesian_update,
if_then_else, analogy_map) + 2 composites + 2 walkable skills + intent
capability migration". The wet-method pattern (Spec 204, applied to the
intent cap) generalizes here: the 4 remaining methods ship with the
optional `run=True` wet path from the start, and the intent-cap
migration (110's deferred task) reuses 204's wiring.

## Done When

- [ ] **The 4 remaining methods ship** (pre_commitment / bayesian_update
      / if_then_else / analogy_map) with the Spec 204 wet `run=True`
      pattern built in. Typed return shape:
      ```python
      ThinkResult = {
        "method":    str,                 # one of the 15 method ids
        "mode":      Literal["scaffold","wet"],
        "scaffold":  dict,                # always present
        "analysis":  dict | None,         # present iff mode == "wet"
        "tokens":    int,                 # via Spec 082/201
        "stop_reason": str | None,        # Driver passthrough when wet
        "reflection_id": str,             # Spec 150 hand-off
      }
      ```
- [ ] **The 2 composites + 2 walkable skills ship** (red-team-pass,
      decision-discipline). Each composite is a deterministic chain of
      methods returning `list[ThinkResult]`. Each walkable skill emits
      ONE phase per call (Spec 114 phase-graph discipline).
- [ ] **Intent-capability migration** (110's deferred task, per Spec
      111) — the 8 intent methods become thin wrappers over the thinking
      cap. Invariant: `intent.<method>(...)` and `thinking.<method>(...)`
      return byte-identical `ThinkResult` payloads under the same seed.
- [ ] **Wet outputs become Reflections** (Spec 150 dogfood loop) — every
      `run=True` call emits a `Reflection(scope="thinking-wet")` whose
      `source_method` field the classifier can group on.
- [ ] **Wet path honors output-budget** (Spec 146) — the scaffold
      portion of `ThinkResult` is byte-deterministic per method+seed
      (the cache-stable prefix); the `analysis` body is the per-call
      variable tail.
- [ ] **Migration parity invariant** — for the intent-cap migration, a
      table-driven test asserts every method's pre- and post-migration
      output graph (Artefact + Reflection nodes) is shape-equal; no
      Reflection lost in the move.
- [ ] **Failure modes** (touches LLM in wet mode):
      `Codes.DRIVER_REFUSAL` from Spec 147; `Codes.WET_TIMEOUT` when
      the Driver exceeds the per-method budget (default 30s);
      `Codes.WET_UNPARSEABLE` when structured output fails schema
      validation (degrade to scaffold + warning Reflection, never
      silent zero); `Codes.METHOD_UNKNOWN` for unknown method ids.
- [ ] **110 row flips toward Shipped** with derived completion %
      (Spec 149 reads the verb + walkable-skill counts off the live
      registry).
- [ ] Test: each new method returns a scaffold (run=False) + a filled
      analysis (run=True, mocked Driver); intent wrappers delegate
      with byte-identical output; migration parity test passes.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  a decision with 3 options and the bayesian_update method
When:   thinking.bayesian_update(prior={A:0.5,B:0.3,C:0.2},
                                  evidence=[...], run=True)
Then:   returns ThinkResult with mode="wet",
        analysis.posterior keys == prior keys,
        sum(analysis.posterior.values()) within 1e-6 of 1.0,
        reflection_id resolvable via analyze.graph_query

Given:  intent.bayesian_update(...) and thinking.bayesian_update(...)
        with the same args + seed
When:   both run
Then:   ThinkResult payloads are byte-identical (migration parity)

Given:  the Driver raises a refusal mid-wet-call
When:   thinking.if_then_else(..., run=True) runs
Then:   degrades to scaffold with stop_reason="driver-refusal",
        mode="scaffold", a Reflection(scope="driver-refusal") emitted,
        never raises to caller
```

## Failure modes (Nygard)

| Failure | Response |
|---|---|
| `DRIVER_REFUSAL` (Spec 147) | degrade to scaffold; emit Reflection(scope="driver-refusal"); never raise |
| `WET_TIMEOUT` (default 30s) | degrade to scaffold with `stop_reason="timeout"` |
| `WET_UNPARSEABLE` (structured output schema fail) | degrade to scaffold + warning Reflection |
| `METHOD_UNKNOWN` | hard error (typed); registry-driven, never silent |
| `COMPOSITE_BUDGET_EXCEEDED` | stop the chain; return partial `list[ThinkResult]` |
| Intent-cap parity broken (migration) | hard fail; rollback the wrapper PR |

## Interconnects

- Spec 204 (intent wet methods) is the pattern this generalizes.
- **Dogfood-loop chain** (150) — wet outputs feed amendment proposals.
- **LLM-driver chain** (147) — wet mode routes through the Driver.
- **Output-budget chain** (146) — scaffold portion is the cache-stable
  prefix; analysis is the per-call tail.
- Spec 111 (capability-migration) governs the intent-cap wrapper move;
  Spec 227 (migration execute) reconciles status + executes the move.
- Spec 149 (derived docs) reads the verb count for the 110 row.
- Spec 225 (prompt cap Slice 2) shares the Driver wiring pattern;
  parity test asserts equivalent failure-mode handling.
- Spec 229 (session-driver Slice 2) `develop.brainstorm` walks these
  methods as a phase-graph — the composites are skill-walkable.

## Open questions

1. Migrate intent cap or deprecate it? **Recommend**: thin-wrapper
   migration (Spec 091's methods stay callable, delegate to thinking).
   Deprecation breaks the wire contract; wrappers are additive.
2. **Wet-mode default per method.** Should `bayesian_update` default
   `run=True` (its scaffold is nearly empty) while `pre_commitment`
   defaults `run=False`? **Recommend**: per-method default declared in
   the verb's signature, driven by "does the scaffold carry useful
   structure" — bayesian/analogy default wet, pre_commitment/if_then
   default scaffold. Documented in each method's docstring.
3. **Composite token cost.** A `red-team-pass` chain of 5 wet calls is
   expensive — cap it? **Recommend**: yes, hard-cap at
   `max_method_tokens * 5` with `Codes.COMPOSITE_BUDGET_EXCEEDED` when
   exceeded; the user can lift the cap explicitly via `budget_override`.
