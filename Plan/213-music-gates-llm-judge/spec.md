---
spec_id: "213"
slug: music-gates-llm-judge
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "100"
depends_on: ["100", "178", "147", "150"]
vision_goals: [4, 6]
affects:
  - agency/capabilities/music/_main.py
  - tests/test_music_gates_judge.py
---

# Spec 213 — music gates: optional judgement findings

## Why

Spec 100 (music-gates) ships 8 decidable gate verbs (audio-release,
catalogue, promo, sub-gates) + the E2E provenance test. The gates are
DECIDABLE — but some quality questions (does this master sound muddy?
does this promo land?) need judgement. Mirroring the analyze judge axis
(Spec 178), the music gates can carry an OPTIONAL judged finding,
clearly tagged, that augments the decidable verdict without replacing it.

## Done When

- [ ] **Each music gate gains an optional `judge=True`** — the Spec 147
      Driver scores the artefact against a rubric, returns a tagged
      `judged` finding; the decidable verdict is unchanged.
- [ ] **Judged findings never block** (advisory) unless the author
      explicitly chains them — the decidable gates stay the hard pass.
- [ ] **Judged findings become Reflections** (Spec 150 dogfood loop).
- [ ] **Degrades** without `[anthropic]` (decidable-only, Spec 100).
- [ ] Test: a gate returns a tagged judged finding (mocked); decidable
      verdict unchanged with/without judge.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 178 (analyze judge axis) is the pattern; **dogfood** (150).
- **LLM-driver chain** (147).

## Open questions

1. Per-gate rubric or shared? **Recommend**: per-gate (audio quality ≠
   promo quality); vendored rubrics, author-overridable.
