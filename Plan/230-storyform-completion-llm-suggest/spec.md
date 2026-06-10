---
spec_id: "230"
slug: storyform-completion-llm-suggest
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "120"
depends_on: ["120", "219", "147", "129"]
vision_goals: [4, 1]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_storyform_completion_llm.py
---

# Spec 230 — storyform-completion LLM suggest

## Why

Spec 120 ships the Dramatica engine completion — 8 new checks +
`novel_coherence_check` composite (exact-fail across 11 fixtures) + the
`storyform-build` 6-phase skill. Spec 219 added `suggest_storyform`.
This applies the same Driver to the COMPLETION path: given a partial
storyform, suggest the missing slots that satisfy `novel_coherence_check`
— the iterate-to-rubric pattern (managed-Outcome style) using the
decidable checks as the rubric.

## Done When

- [ ] **`suggest_completion(storyform_id)`** drives the Spec 147 Driver
      to fill missing storypoints; each iteration runs
      `novel_coherence_check`; loop bounded.
- [ ] **The `storyform-build` skill chains it** as an optional phase.
- [ ] **Output budget honored** (Spec 146); prompt prefix = ontology
      fragments (Spec 129), cache-stable.
- [ ] Test: a partial storyform completes to coherence within bound
      (mocked Driver).
- [ ] TODO row + drift clean.

## Interconnects

- **LLM-driver chain** (147) · Spec 219 (suggest_storyform sibling).
- The decidable checks are the rubric — pattern parity with Spec 224.
