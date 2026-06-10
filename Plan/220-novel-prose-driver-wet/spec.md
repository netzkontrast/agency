---
spec_id: "220"
slug: novel-prose-driver-wet
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "104"
depends_on: ["104", "147", "130", "144"]
vision_goals: [4, 1]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_novel_prose_wet.py
---

# Spec 220 — novel prose TextDriver (wet generation)

## Why

Spec 104 (novel-prose) ships the prose engine + checks. Spec 130
(scene-writer) ships the 5-phase walk but its generate phase is "no
driver binding yet — Slice 2 territory gated on Spec 005", using a
FakeTextDriver stub. Spec 147 lifts the gate: a real TextDriver backed
by the AnthropicDriver generates the scene body from the assembled
brief (Spec 127) or the voice-locked brief (Spec 144), and the shipped
checks validate it.

## Done When

- [ ] **A production TextDriver** behind the Spec 002 boundary, backed
      by Spec 147 — scene-writer phase 3 (generate) uses it; the
      FakeTextDriver stays the CI default.
- [ ] **Generation consumes the voice-locked brief** (Spec 144) when an
      alter is bound, else the plain brief (Spec 127).
- [ ] **The shipped prose checks gate the output** (filter-words,
      show-don't-tell, voice-drift); failures trigger a bounded
      regenerate.
- [ ] **Generation honors the output budget** (Spec 146/154 — a long
      scene captures).
- [ ] Test: scene-writer generates a gate-passing body (mocked Driver);
      Fake fallback unchanged.
- [ ] TODO row + drift clean.

## Interconnects

- **LLM-driver chain** (147) — lands Spec 130's deferred generate phase.
- Spec 144 (voice-locked) + Spec 127 (brief) are the prompt inputs.

## Open questions

1. Stream the scene body? **Recommend**: yes (Spec 146 streaming) —
   scenes exceed the non-streaming token guard.
