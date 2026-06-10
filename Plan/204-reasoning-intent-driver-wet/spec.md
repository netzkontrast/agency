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

- [ ] **Each method gains an optional `run=True`** — the Spec 147
      Driver executes the method against the subject (defaulting to the
      serving intent) and returns the filled structured output
      (`output_config.format`); `run=False` keeps the Spec 091 scaffold.
- [ ] **The filled output is recorded as a Reflection** (feeds Spec 150
      dogfood loop).
- [ ] **Degrades to the scaffold** without `[anthropic]` (Spec 091
      behavior preserved exactly).
- [ ] **Result honors the output budget** (Spec 146).
- [ ] Test: `decompose(run=True)` returns a filled decomposition
      (mocked Driver); `run=False` returns the scaffold unchanged.
- [ ] TODO row + drift clean.

## Interconnects

- **LLM-driver chain** (147) · **dogfood-loop chain** (150) ·
  **output-budget** (146).
- Spec 110 (thinking cap) shares the wet pattern.

## Open questions

1. Wet by default or opt-in? **Recommend**: opt-in (`run=False`
   default) — preserves the lossless scaffold for agents that prefer
   to reason themselves; wet is a convenience.
