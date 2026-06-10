---
spec_id: "161"
slug: skill-first-discovery-llm-rank
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "025"
depends_on: ["025", "068", "147", "146"]
vision_goals: [1, 5]
affects:
  - agency/_discovery.py
  - tests/test_skill_first_discovery.py
---

# Spec 161 — Skill-first discovery with optional LLM rank

## Why

Spec 025 (skill-first-discovery) is Partial — "skill-search ranks above
tool-search; refinement needed per consolidation pass". Tiered
discovery (Spec 068) ships the capability-tier-first surface, but the
RANKING within a tier is lexical. When the `[anthropic]` extra is
present, the Spec 147 Driver can re-rank the top-N candidates by intent
relevance — without ever loading the full tool list (Goal 1) and on a
cache-stable prefix (Spec 146).

## Done When

- [ ] **Skill results rank above verb results** uniformly in `search`
      (close the 025 refinement).
- [ ] **Optional LLM re-rank** — when `[anthropic]`, the top-N (default
      10) candidates are re-ordered by a single structured-output call;
      degrades to lexical when absent.
- [ ] **The re-rank input is the volatile body, never the prefix**
      (Spec 146) — cache holds.
- [ ] Test: a query where the best skill is lexically third surfaces it
      first under LLM rank (mocked Driver); lexical fallback deterministic.
- [ ] TODO row + drift clean.

## Interconnects

- **LLM-driver chain** (147) · **output-budget chain** (146).
- Spec 068 (tiered discovery) is the surface this refines.

## Open questions

1. Re-rank cost vs benefit? **Recommend**: only when query is ambiguous
   (top-2 lexical scores within ε); skip the call otherwise.
