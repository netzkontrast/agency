---
spec_id: "225"
slug: prompt-cap-slice2-llm
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "109"
depends_on: ["109", "147", "082", "201"]
vision_goals: [4, 1]
affects:
  - agency/capabilities/prompt/_main.py
  - tests/test_prompt_cap_slice2.py
---

# Spec 225 — prompt capability Slice 2 (LLM build + optimize)

## Why

Spec 109 (prompt-capability) is Partial — Slice 1 shipped 9 verbs;
Slice 2 names "7 remaining verbs (build, register_builder, optimize,
score_output, analyze_iteration, register_anti_pattern, list_templates,
register_template)". The `optimize` / `score_output` / `analyze_iteration`
verbs are inherently LLM-mediated — they need the Spec 147 Driver. And
109's Followup notes "Approx-token boundary uses 4-chars/token heuristic;
Spec 082 TokenCounter swap deferred" — Spec 201 (API token count) lands
the authoritative count.

## Done When

- [ ] **The 7 Slice-2 verbs ship** — `build`/`optimize`/`score_output`/
      `analyze_iteration` via the Spec 147 Driver (`output_config.format`);
      `register_builder`/`register_anti_pattern`/`register_template` are
      registry writes.
- [ ] **The 4-chars/token heuristic swaps to Spec 082/201 TokenCounter**
      (the deferred 109 task) — authoritative budgets.
- [ ] **Generation honors the output budget** (Spec 146).
- [ ] **109 row flips toward Shipped.**
- [ ] Test: `optimize` improves a fixture prompt's token budget (mocked);
      TokenCounter swap verified.
- [ ] TODO row + drift clean.

## Interconnects

- **LLM-driver chain** (147) · Spec 201 (API token count).
- The prompt cap is the engineering surface the whole charter leans on.

## Open questions

1. Optimize for tokens or quality? **Recommend**: both, as separate
   verbs — `optimize(target="tokens")` vs `optimize(target="quality")`.
