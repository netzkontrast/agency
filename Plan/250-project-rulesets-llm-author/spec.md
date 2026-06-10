---
spec_id: "250"
slug: project-rulesets-llm-author
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "140"
depends_on: ["140", "147", "150", "183"]
vision_goals: [4, 6]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_project_rulesets_author.py
---

# Spec 250 — project rulesets: LLM-authored R-rules

## Why

Spec 140 ships ProjectRule + 4 predicate kinds (mutual-exclusion,
per-scene-budget, forbidden-verbatim, register-forbidden) + the
R-rule registry. Authoring an R-rule from a recurring defect is
exactly the dogfood loop (Spec 150) + opportunity detector (Spec 183)
applied to prose: a recurring sensitivity or voice finding becomes a
proposed R-rule. The Driver authors the rule params; the author confirms.

## Done When

- [ ] **`suggest_r_rule(novel_id, source_findings)`** drives the
      Driver to compose a ProjectRule from recurring findings; output
      = registered rule as `proposal`.
- [ ] **Spec 183 opportunity-detector pipes findings here.**
- [ ] **`run_project_rules` validates** the new rule against the
      source findings before canonization.
- [ ] Test: 5× recurring finding → proposed R-rule that catches the 5
      instances (mocked).
- [ ] TODO row + drift clean.

## Interconnects

- **Dogfood-loop chain** (150) · Spec 183 (opportunity detector).
- **LLM-driver chain** (147).
