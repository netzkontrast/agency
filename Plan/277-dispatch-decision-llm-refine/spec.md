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

- [ ] **`dispatch_decision(..., refine=True)`** — when the 11-signal
      score is in the borderline band, the Spec 147 Driver returns a
      structured `{driver, rationale}` choice; outside the band, the
      decidable heuristic wins unchanged.
- [ ] **Refinements feed Spec 150** — recurring LLM-overrides become
      proposed signal-weight adjustments (the dogfood loop tuning the
      heuristic itself).
- [ ] **Multi-driver (Jules / MA / inline) routed uniformly** (Spec 271).
- [ ] **Decision recorded as a Reflection** with the signal score + the
      LLM rationale.
- [ ] Test: borderline score → LLM picks (mocked); clear score →
      heuristic picks; 3× LLM override → proposed signal adjustment.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 271 (Jules/MA bridge) is the dispatch surface.
- Spec 150 (dogfood) + Spec 258 (quality loop) tune the heuristic.
- **LLM-driver chain** (147).
