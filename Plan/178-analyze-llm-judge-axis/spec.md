---
spec_id: "178"
slug: analyze-llm-judge-axis
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "042"
depends_on: ["042", "147", "166", "150"]
vision_goals: [4, 6]
affects:
  - agency/capabilities/analyze/_judge.py  (NEW)
  - tests/test_analyze_judge.py
---

# Spec 178 — analyze LLM-judge axis (judgement findings)

## Why

Spec 042 ships 4-axis DECIDABLE analysis (quality/security/performance/
architecture) — deliberately no LLM judgement. But many real findings
need judgement (is this abstraction premature? is this naming
misleading?) that decidable rules can't reach. With the Spec 147
Driver, analyze can add an OPTIONAL judgement axis whose findings are
clearly tagged `judged` (not `decidable`), so the two never blur — the
decidable axes stay the trustworthy core, judgement augments.

## Done When

- [ ] **`analyze.run(..., judge=True)`** adds a `judged` axis — the Spec
      147 Driver scores the target against a rubric, returns findings
      with `confidence` + `severity` (`output_config.format`).
- [ ] **Judged findings are tagged distinctly** from decidable ones —
      never merged into the decidable counts; a reviewer sees the
      provenance of each.
- [ ] **Degrades cleanly** without `[anthropic]` (judge axis absent,
      decidable axes unchanged).
- [ ] **Judged findings become `Reflection`s** feeding Spec 150's
      classifier (dogfood loop).
- [ ] Test: judge axis returns tagged findings (mocked Driver);
      decidable counts unchanged with/without judge.
- [ ] TODO row + drift clean.

## Interconnects

- **LLM-driver chain** (147) · **dogfood-loop chain** (150).
- Spec 166 (extras) is the decidable-analyzer sibling.

## Open questions

1. Judge per-file or per-finding? **Recommend**: per-file with a
   bounded finding cap — keeps token cost predictable.
