---
spec_id: "244"
slug: voice-profiles-llm-derive
status: draft
state: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "134"
depends_on: ["134", "147", "138", "144", "137", "150", "254"]
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

- [ ] **`derive_voice_profile(character_id, run=True) -> VoiceProfileProposal`** —
      typed return `VoiceProfileProposal{ character_id, statistical:
      VoiceProfile, judged: VoiceProfile | None, deltas: list[{field,
      stat_value, judged_value, magnitude: float}], scene_sample_ids:
      list[SceneId], driver_model: str, status: Literal["proposal"] }`.
      Driver runs only when scene_sample >= 5 (134 invariant).
- [ ] **Invariant: statistical pass is always populated; judged is
      additive** — `proposal.statistical is not None` for any character
      with >= 5 drafted scenes; `proposal.judged` is None when the
      Driver REFUSALs or skips. Statistical never falls back to judged.
- [ ] **Invariant: deltas surface every divergence** —
      `len(proposal.deltas) == count(field for field in VoiceProfile
      where stat_value != judged_value)`; no silent merging.
- [ ] **Invariant: derived profile lands as `proposal`** (Spec 137); the
      statistical pass remains the decidable default that fills consumer
      verbs until the author confirms the judged delta.
- [ ] **Spec 138 + Spec 144 + Spec 254 consume the upgraded profile
      transparently** — same `VoiceProfile` shape; consumers read
      `confirmed_profile` only, never `proposal`.
- [ ] **Failure modes**: Driver `REFUSAL` on edgy alter content → keep
      statistical, dogfood-emit reason; `BAD_REQUEST` schema violation →
      reject + log to Spec 150; insufficient sample (<5 scenes) → 134's
      hard skip, no Driver call; cache prefix invalidated by sample
      shuffle → re-emit with sorted scene_ids for byte-stability (146).
- [ ] Test: derived profile catches a register shift the statistical
      pass misses (mocked).
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  a character "Mira" with 8 drafted scenes; statistical profile
        shows register=neutral, idiom_density=0.04
When:   derive_voice_profile("char-mira", run=True) called; Driver
        sees scenes 1–4 in cafeteria register, scenes 5–8 in clinical
        register (a shift the average flattens)
Then:   proposal.statistical.register == "neutral";
        proposal.judged.register == "shifting_neutral_to_clinical";
        proposal.deltas contains {field: "register", magnitude > 0.5};
        proposal.status == "proposal";
        consumers (138/144/254) still see the statistical profile until
        author calls confirm_voice_profile(char-mira)
```

## Interconnects

- **LLM-driver chain** (147) — uses canonical AnthropicDriver, structured
  output via `output_config.format`.
- Spec 138 (plural-character) consumes per-alter profiles — judged
  signatures inform PHOBIA_OF + co-front edges.
- Spec 144 (voice-locked brief) reads confirmed profile only for §SYNTAX +
  §LEXICON sections.
- Spec 254 (voice-locked cache) — derived profile sits in the
  alter-stable prefix; re-deriving invalidates the cache once, then
  byte-stable across N scenes.
- Spec 137 (canon locks) — judged profile confirmation mints a Lock
  scoped to `character_id`.
- **Dogfood-loop chain** (150) — judged-vs-statistical disagreement
  patterns become amendment proposals (e.g. "register field needs a
  range, not a literal").

## Open questions

1. **Sample size cap.** Drive on all available scenes or cap?
   **Recommend**: cap at 25 most-recent confirmed scenes — keeps the
   prefix bounded under MAX_PREFIX_TOKENS (146), and stale scenes
   dilute the judged signature.
2. **Re-derive cadence.** Auto re-run after every new scene, or only on
   demand? **Recommend**: on-demand only — auto re-runs burn cache
   prefix invalidations on every scene write.
3. **Judged-only fields.** Are there fields where statistical is
   meaningless (e.g. "emotional cadence")? **Recommend**: yes — tag
   those fields `judged_only` in the VoiceProfile schema so the
   statistical pass leaves them None instead of zero.
