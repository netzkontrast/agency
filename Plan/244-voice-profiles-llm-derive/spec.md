---
spec_id: "244"
slug: voice-profiles-llm-derive
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "134"
depends_on: ["134", "147", "138", "144"]
vision_goals: [4]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_voice_profile_derive.py
---

# Spec 244 — voice-profiles LLM-derived defaults

## Why

Spec 134's defaults "auto-derived from 5+ already-drafted scenes
(computed, not snapshot — rule 8)" — currently statistical. With Spec
147 the Driver can extract richer voice signatures (idiom, register
shifts, emotional cadence) the statistical pass misses; tagged
`judged`, advisory. Spec 138's per-alter VoiceProfile binding and Spec
144's voice-locked brief both benefit.

## Done When

- [ ] **`derive_voice_profile(character_id, run=True)`** runs the
      Driver to extract a richer profile from scenes; structured output.
- [ ] **Derived profile lands as `proposal`** (Spec 137); the
      statistical pass remains the decidable default.
- [ ] **Spec 138 + Spec 144 consume the upgraded profile** transparently.
- [ ] Test: derived profile catches a register shift the statistical
      pass misses (mocked).
- [ ] TODO row + drift clean.

## Interconnects

- Spec 138 (plural-character) + Spec 144 (voice-locked) are consumers.
- **LLM-driver chain** (147).
