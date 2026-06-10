---
spec_id: "224"
slug: novel-gates-llm-judge
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "108"
depends_on: ["108", "178", "122", "150"]
vision_goals: [4, 6]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_novel_gates_judge.py
---

# Spec 224 — novel gates: optional judgement findings

## Why

Spec 108 (novel-gates) ships the decidable publication gates. The
editorial pipeline (Spec 122) is also decidable (filter-words,
show-don't-tell, continuity). But developmental questions (does the
midpoint land? is the antagonist's arc satisfying?) need judgement.
Mirroring the analyze judge axis (Spec 178) + the music gates (Spec
213), the novel gates can carry an OPTIONAL judged finding, tagged,
augmenting the decidable verdict.

## Done When

- [ ] **Each novel gate gains an optional `judge=True`** — the Spec 147
      Driver scores against a rubric, returns a tagged `judged` finding;
      the decidable verdict unchanged.
- [ ] **Judged findings never block** unless explicitly chained (the
      decidable gates stay the hard pass).
- [ ] **Judged findings become Reflections** (Spec 150 dogfood loop) —
      e.g. a recurring "weak midpoint" judgement across chapters becomes
      an amendment proposal.
- [ ] **Degrades** without `[anthropic]` (Spec 108 decidable-only).
- [ ] Test: a gate returns a tagged judged finding (mocked); decidable
      verdict unchanged.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 178 (analyze judge) + Spec 213 (music gates judge) are the
  pattern · **dogfood** (150).
- Spec 122 (editorial) is the decidable sibling.

## Open questions

1. Per-gate rubric? **Recommend**: yes — developmental ≠ line ≠ copy
   judgement; vendored, author-overridable.
