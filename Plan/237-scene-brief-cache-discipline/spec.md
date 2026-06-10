---
spec_id: "237"
slug: scene-brief-cache-discipline
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "127"
depends_on: ["127", "146", "147", "201"]
vision_goals: [1]
affects:
  - agency/capabilities/prompt/_main.py
  - tests/test_scene_brief_cache.py
---

# Spec 237 — scene-brief cache discipline

## Why

Spec 127 ships `assemble_scene_brief` (7 graph-backed sections, token-
budgeted to 2000). Per the `claude-api` skill, prompt caching works
when the prefix is BYTE-STABLE — but the brief currently orders
sections by graph traversal order, and varies prefix bytes per call
when a section's source data shifts. With Spec 146 prefix discipline
and Spec 201 authoritative token count, the brief gains explicit cache
hygiene: stable sections first, volatile sections after the last
breakpoint, every call counted.

## Done When

- [ ] **Section order = stability-descending** (frozen ontology
      fragments → semi-stable codex → volatile scene-state).
- [ ] **`cache_control` breakpoint** placed at the last stable section
      (per claude-api skill: max 4 breakpoints, ≥1024-token minimum).
- [ ] **Token counts via Spec 201** when the Driver is the consumer.
- [ ] **Verify cache hits** in the test — second call shows
      `cache_read_input_tokens > 0` on a mocked Driver.
- [ ] Test: prefix bytes stable across 5 calls with identical scene id.
- [ ] TODO row + drift clean.

## Interconnects

- **Output-budget chain** (146) anchor consumer.
- Spec 147 + Spec 201 for measured budgets.
