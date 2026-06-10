---
spec_id: "187"
slug: lint-token-rules-output-side
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "067"
depends_on: ["067", "146", "154", "186"]
vision_goals: [1]
affects:
  - agency/_lints/
  - tests/test_output_token_lints.py
---

# Spec 187 — output-side token-economy lint rules

## Why

Spec 067 ships the executable token-economy goal-test — but only over
NAMES (`name_token_budget`, `bare_name_*`, `prefix-dominance`). The
output side (the bytes returned to an LLM driver) has no lint. This
spec adds the output-side rules so the same lint pipeline that guards
name economy guards response economy.

## Done When

- [ ] **`response_prefix_stable` lint** (the Spec 146 discipline, in
      the 067 pipeline) — fails when a substrate-tool prefix
      interpolates non-deterministic content.
- [ ] **`overflow_capture_present` lint** — a verb whose result can
      exceed the budget must route through Spec 154 capture (not
      silent truncation).
- [ ] **`fields_projectable` lint** — a CLI-exposed verb's result is a
      flat-enough dict that `--fields` (Spec 160) can project it.
- [ ] **All three are relationship/invariant rules** (rule 8), not
      pinned byte caps (except documented tunable budgets).
- [ ] Test: each lint trips its fixture; the live registry passes.
- [ ] TODO row + drift clean.

## Interconnects

- **Output-budget chain** (146/154/160): these are its lints.
- Spec 067 is the pipeline; Spec 186 the cluster charter.

## Open questions

1. WARN or error first? **Recommend**: WARN one cycle then promote
   (the 056/058/171/173 pattern), per-rule.
