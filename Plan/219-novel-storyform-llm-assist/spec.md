---
spec_id: "219"
slug: novel-storyform-llm-assist
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "103"
depends_on: ["103", "147", "129", "136"]
vision_goals: [4, 1]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_novel_storyform_llm.py
---

# Spec 219 — novel storyform LLM-assisted authoring

## Why

Spec 103 ships the Dramatica engine (11 decidable + 2 hybrid checks) +
the 304-entry ontology. Authoring a storyform — picking the 75+ NCP
storypoints coherently — is hard, and currently the author fills it by
hand against the checks. With the Spec 147 Driver + the prompt
fragments (Spec 129), `suggest_storyform(premise)` can propose a
coherent NCP the decidable checks then validate, and (with Spec 136)
suggest the dual-storyform inversion partner.

## Done When

- [ ] **`suggest_storyform(premise, ...)`** drives the Spec 147 Driver
      with the premise + the Spec 129 fragments to propose an NCP;
      `novel_coherence_check` (Spec 120) validates it; failures feed
      back for a bounded re-propose.
- [ ] **Dual-storyform suggestion** (Spec 136) — propose the Klein-c
      inversion partner for a given storyform.
- [ ] **The ontology prefix is cache-stable** (Spec 146) across
      suggestions.
- [ ] **Degrades** to the manual checks without `[anthropic]` (Spec 103).
- [ ] Test: a suggested storyform passes coherence (mocked Driver);
      the inversion partner check holds.
- [ ] TODO row + drift clean.

## Interconnects

- **LLM-driver chain** (147) · Spec 129 (fragments) · Spec 136
  (dual-storyform) for the inversion partner.

## Open questions

1. One-shot or iterate-to-coherent? **Recommend**: iterate (the checks
   are the rubric — a managed-Outcome-style loop fits).
