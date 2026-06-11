---
spec_id: "277"
slug: dispatch-decision-llm-refine
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "040"
depends_on: ["040", "147", "271", "150"]
vision_goals: [1, 6]
affects:
  - agency/capabilities/delegate/_main.py
  - tests/test_dispatch_llm_refine.py
---

# Spec 277 — dispatch-decision: LLM-refined 11 signals

## Why

Spec 040 ships the 11-signal heuristic + cache/Jules budget model. The
signals are well-tuned for the documented work shapes but real tasks
fall between. With the Spec 147 Driver, a refinement Matcher can break
ties — when the 11-signal score is within ε of the boundary, an LLM
call with structured output decides; the decidable heuristic stays the
primary gate; the LLM only adjudicates the borderline cases. Spec 271
extends the dispatch options (Jules + MA + future drivers); the
refinement applies uniformly.

## Done When

- [ ] **The 11-signal heuristic stays the PRIMARY gate.** Two
      disqualifiers (S6 mutates without provenance, S11 budget gate)
      and the positive-signal aggregate run UNCHANGED from Spec 040.
      The LLM never sees a non-borderline case.
- [ ] **Borderline band is precision-defined**, not vibes. A case is
      borderline iff `abs(positive_signal_score - boundary) <= ε` AND
      no disqualifier fires. Default `ε=1` (one signal's worth) with
      `boundary=1` (the "any positive signal → dispatch" line). Both
      tunable via `delegate.config.refine_epsilon`. Outside the band:
      heuristic wins, LLM never invoked.
- [ ] **`dispatch_decision(..., refine=True)`** — when the case IS
      borderline, the Spec 147 Driver returns a structured
      `{driver: Literal["inline","jules","managed_agent",...], rationale:
      str, confidence: float}` via `output_config.format`. Outside the
      band, `refine=True` is a no-op (heuristic wins; the LLM call is
      skipped to preserve the cost model).
- [ ] **Hard floor — LLM cannot override a disqualifier.** A mutating
      task without provenance NEVER routes remote regardless of LLM
      output. The LLM is asked only "which driver" / "inline vs
      dispatch", never "ignore the safety gate".
- [ ] **Refinements feed Spec 150** — recurring LLM-overrides on the
      same case-shape become proposed signal-weight adjustments. The
      tuning loop is: LLM repeatedly disagrees with heuristic on a
      shape → Spec 150 proposes a weight tweak → human reviews →
      heuristic updates → LLM no longer asked for that shape.
- [ ] **Multi-driver (Jules / MA / inline) routed uniformly** (Spec
      271) — the LLM's `driver` enum is derived from the registered
      `RemoteDriver` set, not a hand-pinned list.
- [ ] **Decision recorded as a Reflection** with `{signal_score,
      borderline: bool, llm_invoked: bool, llm_rationale: str | None,
      chosen_driver, prompt_cache_hit: bool}`. The Reflection is the
      audit trail.
- [ ] **Invariants** (CLAUDE.md rule 8):
      - `count(LLM_invocations) <= count(borderline_cases)` — LLM only
        runs on borderline.
      - For every dispatch decision with a disqualifier firing,
        `chosen_driver ∈ {inline, recovery_path}` regardless of LLM
        output — safety gate dominates.
      - For every non-borderline case, the heuristic's choice
        equals the recorded chosen_driver (the LLM had no say).
      - LLM driver-enum = `set(RemoteDriver.registered) ∪
        {inline}` — open-set per Spec 271; no hardcoded list.
- [ ] **Failure modes table** — see below.
- [ ] Test: borderline score → LLM picks (mocked); clear score → LLM
      NOT invoked (cost preserved); disqualifier fires + LLM picks
      remote → chosen_driver still inline (safety floor); 3× LLM
      override on the same case-shape → Spec 150 proposes a signal
      adjustment; new driver registers → LLM enum widens automatically.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  intent with signal score = 1.2 (just above boundary=1), ε=1,
        no disqualifier — case IS borderline (|1.2 - 1| = 0.2 ≤ 1)
When:   dispatch_decision(refine=True) runs
Then:   Spec 147 Driver invoked with the case shape + signal
        breakdown; structured output returns {driver: "inline",
        rationale: "exploration is shallow; cache_overlap dominates",
        confidence: 0.78}; chosen_driver=inline; Reflection records
        {borderline: True, llm_invoked: True, ...}

Given:  intent with signal score = 5.0 (clear dispatch — far above
        boundary)
When:   dispatch_decision(refine=True) runs
Then:   LLM NEVER invoked (cost preserved); heuristic picks jules per
        Spec 040 matrix; Reflection records {borderline: False,
        llm_invoked: False, ...}

Given:  mutating intent (S6=1 disqualifier) with borderline positive
        score = 1.2 and LLM (asked anyway as audit) suggests
        "managed_agent"
When:   dispatch_decision runs
Then:   disqualifier dominates — chosen_driver=inline regardless of
        LLM output; Reflection records the LLM suggestion + the
        override; safety floor never breached

Given:  over 30 days, 5 borderline cases of shape "S2=1, S5=1, S9=low"
        all see LLM override to jules where heuristic would inline
When:   Spec 150 mining pass runs
Then:   AmendmentProposal: "raise S2+S5 combined weight by 0.5";
        human reviews; if accepted, heuristic updates; subsequent
        same-shape cases are non-borderline and the LLM stops being
        invoked for them
```

## Failure modes

| # | Failure | Detection | Response |
|---|---|---|---|
| F1 | LLM returns a `driver` not in the registered set | Schema validation on structured output | Fall back to heuristic choice; emit `llm_invalid_driver` MonitorEvent; do NOT crash dispatch |
| F2 | LLM call times out (slow network, API issue) | Per-call timeout (default 3s) | Fall back to heuristic choice; emit `llm_refine_timeout`; preserve dispatch latency budget |
| F3 | LLM attempts to override a disqualifier | Post-LLM safety check | Disqualifier wins; LLM suggestion logged but NOT acted on; emit `llm_override_blocked` |
| F4 | Borderline band too wide → LLM cost explosion | Cost metric on `count(LLM_invocations) / count(decisions)` | Auto-narrow ε; doctor surfaces the trend; Spec 150 proposes a permanent ε tune |
| F5 | LLM consistently picks same driver regardless of signals | Mining pass on rationale → driver correlation | The model isn't actually deciding; Spec 277-style audit flags; revisit the prompt |
| F6 | Driver registry changes mid-session (new driver) | Enum staleness check before LLM call | Refresh enum from registry on each invocation; never cache stale driver list |
| F7 | Recurring LLM-override on same shape but heuristic untouched | Spec 150 detects + no amendment lands | Time-to-amendment metric (Spec 258) flags; doctor surfaces the unconverged loop |

## Interconnects

- Spec 040 (parent) — 11-signal heuristic stays primary.
- Spec 147 (AnthropicDriver) provides the structured-output LLM call.
- Spec 271 (Jules/MA bridge) provides the open-set driver enum.
- Spec 150 (dogfood classifier) tunes the heuristic from recurring
  overrides.
- Spec 258 (loop quality) measures time-to-convergence.
- Spec 274 (structured monitor) records `llm_invoked`,
  `llm_override_blocked`, `llm_refine_timeout` events for postmortem.
- Spec 275 (Jules monitor amendment loop) is a sibling consumer of
  Spec 150 — recurring patterns from BOTH dispatch + monitor feed the
  same proposal pipeline.
- Spec 276 (doctor managed-aware) reads driver readiness; an
  unavailable driver is excluded from the LLM's enum.
- **LLM-driver chain** (147) + **Dogfood-loop chain** (150) — this
  spec sits at the intersection.

## Open questions

1. **Borderline-band tuning cadence.** Should ε auto-adjust based on
   cost vs accuracy? **Recommend**: ε is a tunable budget (CLAUDE.md
   rule 8) — documented config, not auto-tuned. Spec 150 proposals
   are how it changes; auto-tuning invites runaway.
2. **LLM rationale storage.** Persist full text per Reflection, or
   summary only? **Recommend**: full text — it's the audit trail for
   Spec 150 mining; storage cost is bounded by `count(borderline)`,
   which is small by design.
3. **What about a "third opinion" — multiple LLM calls?**
   **Recommend**: NO — one call, one structured output. Doubling the
   cost for marginal accuracy gain on already-borderline cases is the
   wrong trade; let the dogfood loop tune the heuristic instead.
