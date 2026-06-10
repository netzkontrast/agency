---
spec_id: "134"
slug: pov-voice-profiles
status: draft
last_updated: 2026-06-10
owner: "@agency"
depends_on: ["101", "104", "122", "130", "131"]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_novel_voice_profiles.py
domain: novel / character / voice
parent_spec: "101"
mvp-source:
  - "Spec 130 scene-writer phase 4 check carve-out — no per-POV voice check today"
  - "Spec 122 `check_voice_consistency` is chapter-level; needs per-character refinement"
---

# Spec 134 — POV voice profiles (per-character voice signature)

## Why

Spec 122's `check_voice_consistency` flags chapters whose voice
signature outlies the manuscript baseline — but it treats the
manuscript as ONE voice. Multi-POV novels (the common case) need
per-POV voice signatures: Eliza's chapters should sound like Eliza,
not like the average of Eliza + Marcus + the omniscient narrator.

Spec 131 introduced `pov_character_id` on Scene; Spec 130 ships the
scene-writer skill's check phase. Without per-POV voice profiles, the
check is shape-only — "the prose is consistent with itself" — not
"this prose sounds like Eliza."

## Done When

- [ ] **`VoiceProfile` node**:
      ```
      {character_id, vocabulary_floor: int, sentence_avg_target: float,
       sentence_avg_stddev: float, taboo_words: csv, signature_phrases: csv,
       formality_target: "low"|"medium"|"high", contractions: bool}
      ```
      - `vocabulary_floor`: minimum unique-word ratio (deviation from
        average → too restricted vocabulary for this character)
      - `sentence_avg_target` + `sentence_avg_stddev`: bell-curve target
        for sentence length
      - `taboo_words`: comma-list this character would never say
        (a duchess says "cannot", a sailor says "can't")
      - `signature_phrases`: phrases the character DOES say
        ("by the rivers of Babylon", "in three shakes")
      - `formality_target`: documented tunable (low = contractions OK,
        casual vocab; high = no contractions, elevated vocab)
      - `contractions`: explicit flag (some characters never use them)
- [ ] **`VOICE_OF` edge**: VoiceProfile → Character (the per-character
      voice signature; one VoiceProfile per Character — overwrite on
      update).
- [ ] **6 verbs on `novel` cap**:
      - `create_voice_profile(character_id, **fields)` — mints
        VoiceProfile + VOICE_OF edge.
      - `update_voice_profile(character_id, **fields)` — partial update
        of any field.
      - `get_voice_profile(character_id) -> profile dict | NOT_FOUND`.
      - `score_voice_match(character_id, body) -> {score: 0-100,
        deviations: [{field, target, actual, severity}]}` — computes
        deviation across the profile fields; lower score = bigger drift.
      - `check_pov_voice(scene_id) -> {pass, score, deviations}` —
        gates a scene against its POV character's profile. Reads
        `Scene.pov_character_id` (Spec 131) and `Scene.body`. Default
        pass threshold: 70.
      - `voice_drift_report(novel_id) -> {by_character: {character_id:
        [{scene_id, score}]}, manuscript_outliers: [{scene_id, score}]}`
        — full-manuscript audit; sorts each character's scenes by score;
        flags the bottom 10% as outliers needing revision.
- [ ] **Spec 130 scene-writer skill phase 4 extension**: `check`
      phase verbs list extended with `novel.check_pov_voice` (already a
      check; just appears in the chain). When phase 4 runs, it also
      checks the scene body against the POV character's voice profile.
- [ ] **`voice_drift_gate(novel_id, min_score=70)`** composite gate
      verb: passes IFF every scene with `pov_character_id` set scores ≥
      min_score against its profile. Drops into the editorial-pipeline
      (Spec 122) as a Slice-2 hook to `line_gate`.
- [ ] **Computed values, not snapshots**: per CLAUDE.md rule 8,
      `sentence_avg_target` defaults are derived from the character's
      already-drafted scenes when the profile is created (5+ scenes
      required for auto-derivation; below that, the author authors it
      directly).
- [ ] TODO row + drift clean.

## Design notes

- **One profile per character**. Voice can DRIFT over a manuscript
  (Eliza in chapter 1 vs Eliza in chapter 30 after her arc) — that's
  expected; the profile captures the dominant voice. Out-of-position
  arc-driven shifts are author-authorized exceptions (drop the threshold
  for those scenes via a `_voice_exception` Scene property — Slice 2).
- **Soft severity is the rule**: voice drift is a *warning*, never a
  hard gate. Authors override; the system surfaces.
- **Signature_phrases is opt-in**: empty list is fine; the score
  ignores the field when empty.

## Open questions

1. **Auto-derivation threshold**: 5 scenes minimum to compute defaults?
   Smaller → noisy; larger → late to be useful. *Recommend*: 5.
2. **Score weighting**: equal-weighted across fields, or
   author-tunable? *Recommend*: equal-weighted v1 (avoid premature
   tunability); add a `weights` dict in Slice 2.
3. **Should `taboo_words` matches be hard violations (score = 0) or
   weighted?** *Recommend*: hard-violation per word found; the
   character literally said something they wouldn't. Author can override
   via `update_voice_profile` to remove the word from taboo.

## Followup

(Populated when the PR ships.)
