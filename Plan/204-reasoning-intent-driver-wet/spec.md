---
spec_id: "204"
slug: reasoning-intent-driver-wet
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "091"
depends_on: ["091", "147", "110", "146"]
vision_goals: [1, 6]
affects:
  - agency/capabilities/intent.py
  - tests/test_intent_driver_wet.py
---

# Spec 204 — reasoning capability wet methods

## Why

Spec 091 ships the `intent` capability — eight critical-thinking methods
(decompose/assumptions/premortem/…), each returning a structured
SCAFFOLD the agent fills "in chat — but lossy" (the exact phrasing the
charter flags). Spec 110 ships more methods, same scaffold pattern.
With the Spec 147 Driver, a method can OPTIONALLY run the reasoning and
return the filled analysis (not just the scaffold) — making the
critical-thinking surface productive, not just prompt-shaped, and
keeping the result on a cache-stable, budgeted surface.

## Done When

- [ ] **`ReasoningResult` typed return** — `ReasoningResult = {method,
      subject_intent_id, mode: Literal["scaffold","wet"], scaffold:
      dict, filled: dict | None, driver_used: bool,
      reflection_node_id: str | None, payload_tokens: int}`. The
      scaffold is always present (lossless); `filled` is non-None only
      when `mode=="wet"` succeeded.
- [ ] **Each method gains an optional `run=True`** — the Spec 147
      Driver executes the method against the subject (defaulting to the
      serving intent) and returns the filled structured output
      (`output_config.format`); `run=False` keeps the Spec 091 scaffold.
- [ ] **Invariant — scaffold is lossless** (relationship): for every
      method M, `ReasoningResult(run=False).scaffold ==
      ReasoningResult(run=True).scaffold` — the wet path NEVER mutates
      the scaffold, only fills alongside.
- [ ] **Invariant — wet preserves scaffold keys** (relationship): for
      every `(method, subject)`, `filled.keys() == scaffold.keys()` —
      the Driver may not invent new top-level keys (schema-locked by
      `output_config.format`).
- [ ] **Invariant — graceful degradation** (relationship): when
      `[anthropic]` is not installed, `run=True` returns
      `ReasoningResult{mode:"scaffold", filled:None,
      driver_used:false}` instead of raising — the call site doesn't
      need to branch on the extra.
- [ ] **Invariant — provenance edge**: every `mode=="wet"` result
      writes `(Invocation)-[:PRODUCES]->(Reflection)` AND
      `(Reflection)-[:SERVES]->(Intent)` — both edges traversed by
      Spec 150 amendment classifier.
- [ ] **Invariant — output budget** (relationship): `payload_tokens <=
      MAX_REASONING_PAYLOAD_TOKENS` (default 4000); over-budget filled
      results are truncated with a `truncated=true` flag, scaffold
      always preserved.
- [ ] **Failure mode coverage** — Driver REFUSAL / RATE_LIMITED /
      TIMEOUT / schema violation each yield `mode:"scaffold"` with a
      typed `error_code`; the scaffold is delivered regardless.
- [ ] Test: `decompose(run=True)` returns a filled decomposition
      (mocked Driver); `run=False` returns the scaffold unchanged;
      degradation deterministic; provenance edges queryable via Spec 203.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  intent "build the parity gate" + method "premortem" +
        [anthropic] installed
When:   intent.premortem(intent_id, run=True) runs
Then:   ReasoningResult{mode:"wet", scaffold:{risks:[...], mitigations:[
            ...]}, filled:{risks:[3 items], mitigations:[3 items]},
            driver_used:true, reflection_node_id:"refl_..."}
        AND filled.keys() == scaffold.keys()
        AND graph has (Invocation)-[:PRODUCES]->(Reflection)
            -[:SERVES]->(Intent{id:intent_id})

Given:  same intent, run=False
When:   intent.premortem(intent_id, run=False) runs
Then:   ReasoningResult{mode:"scaffold", scaffold:{...}, filled:None,
            driver_used:false, reflection_node_id:None}
        AND scaffold bytes are byte-stable across calls (Spec 146)

Given:  [anthropic] not installed AND run=True
When:   intent.premortem(intent_id, run=True) runs
Then:   ReasoningResult{mode:"scaffold", filled:None,
            driver_used:false, error_code:"anthropic_not_installed"}
        — never raises; caller branches on `mode`, not on the extra
```

## Failure modes (Nygard)

| Failure | Method response |
|---|---|
| Driver `REFUSAL` (Spec 147) | scaffold delivered; `error_code:"REFUSAL"`; no reflection edge |
| Driver `RATE_LIMITED` | retry per Spec 147 budget; on exhaustion, scaffold + error_code |
| Driver `TIMEOUT` | scaffold; `error_code:"TIMEOUT"` |
| `output_config.format` schema violation | re-issue once with stricter schema; on second fail, scaffold + WARN |
| Filled output exceeds budget | `truncated=true` flag on `filled`; scaffold always intact |
| Driver invents new top-level keys | hard invariant fail; scaffold returned instead |
| Subject intent not found | typed `BAD_REQUEST{detail:"intent_id"}` — never fabricate |

## Interconnects

- **LLM-driver chain** (147) · **dogfood-loop chain** (150) ·
  **output-budget** (146).
- Spec 110 (thinking cap) shares the wet pattern — same `run=` flag,
  same lossless-scaffold rule.
- Spec 200 (adaptive walk) — shares the `driver_used` / `fallback_reason`
  envelope shape; consistency across the LLM-optional surface.
- Spec 203 (graph query) — wet-mode reflections are queryable via the
  moat query (`Reflection SERVES Intent` edge path).
- Spec 150 (dogfood classifier) — every wet reflection is a classifier
  input; amendment proposals trace back via `reflection_node_id`.
- Spec 199 (skill round-trip) — each `intent.*` method is itself a
  published skill; its Use-when description gates loading.

## Open questions

1. Wet by default or opt-in? **Recommend**: opt-in (`run=False`
   default) — preserves the lossless scaffold for agents that prefer
   to reason themselves; wet is a convenience, not a regression to
   black-box reasoning.
2. Per-method scaffold schemas — hand-authored or derived?
   **Recommend**: derived from the method's docstring `Output:` block
   (CLAUDE.md rule 8 — no hand-authored schema constants); Spec 149
   drift gates divergence.
3. How does the engine surface wet-mode telemetry (cost, latency)?
   **Recommend**: `ReasoningResult.driver_meta = {model, usage,
   latency_ms}` when `driver_used=true`; `agency_doctor` aggregates
   per-method counters for visibility.
