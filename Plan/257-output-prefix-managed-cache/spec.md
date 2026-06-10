---
spec_id: "257"
slug: output-prefix-managed-cache
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "146"
depends_on: ["146", "237", "254", "201"]
vision_goals: [1]
affects:
  - agency/_envelope.py
  - tests/test_managed_cache_proof.py
---

# Spec 257 — output-prefix: Managed-Agents cache proof

## Why

Spec 146 anchors the output-budget chain. The Managed-Agents surface
(claude-api skill) provides built-in prompt caching + context
compaction. The engine's prefix discipline should compose with
Managed-Agents caching for the harness-in-harness path: when the
engine is wrapped in a Managed-Agent session, the prefix-stable
substrate-tool responses cache correctly through the session boundary.

## Done When

- [ ] **Cross-session prefix-stability test** — engine response prefix
      identical across two Managed-Agent sessions sharing an agent.
- [ ] **Compaction-block preservation** — substrate-tool responses
      survive compaction (the `response.content` discipline from
      claude-api skill).
- [ ] **Documented compose pattern** in the engine for users wrapping
      agency in a Managed-Agents harness.
- [ ] Test: prefix bytes stable across mocked Managed-Agents sessions;
      compaction preserves the substrate-tool envelope.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 146 (parent) · Spec 237 + Spec 254 sibling cache disciplines.
- **Output-budget chain** completion across the MA bridge.
