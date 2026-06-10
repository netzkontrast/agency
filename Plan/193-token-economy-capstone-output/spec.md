---
spec_id: "193"
slug: token-economy-capstone-output
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "074"
depends_on: ["074", "186", "187", "146"]
vision_goals: [1]
affects:
  - tests/test_token_economy_capstone.py
  - docs/vision/GOALS.md
---

# Spec 193 — token-economy capstone, output-side proof

## Why

Spec 074 is the token-economy cluster capstone — it proved the
input/discovery economy goal met. The enhancement charter adds the
output side (Specs 146/154/160/186/187). The capstone should be
re-run with the output-side invariants included, producing the
end-to-end proof: a wrapping LLM driver sees a cache-stable prefix, a
budgeted body, and a recall handle for overflow — the full token-economy
story Goal 1 promises.

## Done When

- [ ] **End-to-end capstone test** — a simulated LLM-driver session
      over the engine measures: cache-hit rate on repeated discovery
      (Spec 146 prefix), zero silent truncation (Spec 154 capture),
      field-projected results (Spec 160).
- [ ] **The proof is relationships** (rule 8): `cache_read > 0` on the
      second call, `truncated ⇒ recall_handle present`, etc. — no pinned
      token counts.
- [ ] **GOALS.md Goal-1 row updated** to cite the output-side proof.
- [ ] Test: the capstone session asserts all three invariants.
- [ ] TODO row + drift clean.

## Interconnects

- **Output-budget chain** (146/154/160): this is its end-to-end proof.
- Spec 186 (cluster charter) + Spec 187 (lints) are the companions.

## Open questions

1. Live API in the capstone, or simulated? **Recommend**: simulated
   (deterministic, no API cost) for CI; a tagged live variant validates
   real cache behavior.
