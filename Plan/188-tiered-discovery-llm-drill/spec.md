---
spec_id: "188"
slug: tiered-discovery-llm-drill
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "068"
depends_on: ["068", "161", "146", "147"]
vision_goals: [1, 5]
affects:
  - agency/_discovery.py
  - tests/test_tiered_discovery_drill.py
---

# Spec 188 — tiered-discovery LLM-assisted drill

## Why

Spec 068 ships tiered discovery (−83% discovery tokens) — capability
tier first, drill into a capability for its verbs. The DRILL decision
(which capability to drill into) is currently the agent's job from the
one-line summaries. When the Spec 147 Driver is present, `search` can
suggest the most likely capability to drill into for a free-text query —
saving the round trip — while still never loading the full verb list
(Goal 1) and on a cache-stable prefix (Spec 146).

## Done When

- [ ] **`search(query, suggest_drill=True)`** returns the tier list
      PLUS a suggested capability to drill into (Spec 147 structured
      output), with the verbs of ONLY that capability pre-expanded.
- [ ] **The pre-expansion respects the budget** — one capability's
      verbs, not all (Goal 1 preserved).
- [ ] **Degrades to plain tiered discovery** without `[anthropic]`.
- [ ] **The −83% baseline is not regressed** — measured (Spec 149),
      not re-pinned.
- [ ] Test: a query drills into the right capability (mocked Driver);
      token count stays under the tiered baseline.
- [ ] TODO row + drift clean.

## Interconnects

- **LLM-driver chain** (147) · **output-budget chain** (146).
- Spec 161 (discovery rank) is the sibling LLM-assist.

## Open questions

1. Pre-expand one capability or top-2? **Recommend**: one (the budget
   discipline); the agent drills further if wrong.
