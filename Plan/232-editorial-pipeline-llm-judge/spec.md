---
spec_id: "232"
slug: editorial-pipeline-llm-judge
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "122"
depends_on: ["122", "178", "224", "150"]
vision_goals: [4, 6]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_editorial_llm_judge.py
---

# Spec 232 — editorial pipeline: optional judged findings

## Why

Spec 122 ships 5 decidable prose checks + 3 editorial-stage gates + 2
walkable skills (developmental-editor / line-editor). The decidable
checks miss judgement-level findings (pace, voice authenticity, theme
landing). Mirroring Spec 178 (analyze judge axis) and Spec 224 (novel
gates judge), the editorial checks gain an optional `judge=True`,
tagged distinctly, feeding the dogfood loop.

## Done When

- [ ] **Each `check_*` gains `judge=True`** — judged findings tagged.
- [ ] **Developmental-editor + line-editor walks chain optional judge
      phases** (advisory, never block unless explicit).
- [ ] **Judged findings → Reflections** (Spec 150).
- [ ] **Output budget honored** (Spec 146).
- [ ] Test: gate returns tagged judged finding; decidable unchanged.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 178 + Spec 224 are the pattern · **dogfood** (150).
