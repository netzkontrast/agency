---
spec_id: "208"
slug: music-lyrics-llm-generation
status: draft
state: draft
last_updated: 2026-06-11
owner: "@agency"
enhances: "095"
depends_on: ["095", "147", "146", "150", "206", "213", "216"]
vision_goals: [4, 1]
affects:
  - agency/capabilities/music/_main.py
  - agency/capabilities/music/clusters/lyrics.py
  - tests/test_music_lyrics_llm.py
---

# Spec 208 — music lyrics LLM generation

## Why

Spec 095 (music-lyrics) ships 16 verbs + 5 templates for lyric
STRUCTURE + gates (rhyme, prosody, explicit) — but the actual lyric
WRITING is the agent's job in chat. The bitwize-music lyric-writer skill
is a prompt; the agency port should make it a verb: `write_lyrics` runs
the Spec 147 Driver against the track concept + voice + the structural
templates, returns drafted lyrics the existing gates then check.

## Done When

- [ ] **`write_lyrics(track_id, voice_profile_id, max_iterations=3)`**
      drives the Spec 147 Driver with the track concept, the 095
      templates, and the voice profile; returns lyrics the shipped gates
      (rhyme/prosody/explicit) validate. Typed return:
      `LyricResult = {track_id, lyrics_md: str, iterations: int,
      gate_verdicts: list[GateVerdict], driver_usage: TokenUsage,
      reflection_id: NodeId}`.
- [ ] **Generation honors the output budget** (Spec 146) — the prompt
      prefix (templates + voice profile) is cache-stable across tracks
      in the same album; only the per-track concept varies in `body`.
- [ ] **Drafts record provenance** + a Reflection (Spec 150) so lyric
      iterations feed the dogfood loop; the `Artefact PRODUCES` edge
      links the lyric node back to the originating intent.
- [ ] **Iterate-to-gate loop** — generate, run all gates, regenerate on
      fail with the failing-gate hints folded into the next prompt;
      bounded by `max_iterations`.
- [ ] **Degrades** without `[anthropic]` (returns the structured
      template scaffold, Spec 095 behavior); the verb still emits a
      `LyricResult` with `lyrics_md` set to the scaffold and
      `gate_verdicts=[]`.
- [ ] **Test**: `write_lyrics` returns gate-passing lyrics (mocked Driver).
- [ ] **TODO row + drift clean.**

## Measurable invariants (relationships, not pinned counts)

- **Gate convergence** — for a successful return, `all(v.passed for v in
  gate_verdicts) == True`; for a failed return, `iterations ==
  max_iterations` (no false "pass" without all gates green).
- **Prompt-prefix stability** — across two `write_lyrics` calls for
  different tracks of the SAME album, the system-prompt prefix bytes
  are identical (Spec 146 cache-hit condition).
- **Provenance density** — every returned `LyricResult` has exactly one
  `reflection_id` AND `>= 1` artefact node with `PRODUCES` edge to the
  track intent (no lyric without provenance).
- **Iteration-cost monotonicity** — `driver_usage.input_tokens` grows
  monotonically across retries (each retry adds the prior failing
  verdicts as context), never resets.

## Worked example (Given/When/Then)

```text
Given:  track_id with concept="late-night drive, regret", voice_profile_id
        for a tenor narrator, AnthropicDriver mocked to return a 3-verse
        lyric that passes rhyme + prosody but fails explicit-checker
        on iteration 1, then passes all gates on iteration 2
When:   write_lyrics(track_id, voice_profile_id, max_iterations=3)
Then:   returns LyricResult{iterations=2, gate_verdicts=[rhyme.passed,
        prosody.passed, explicit.passed], reflection_id≠None}
        AND analyze.graph(reflection_id) shows "regenerated due to
        explicit-checker failure" in the Reflection text
        AND the cache prefix bytes match a second call on a sibling track
```

## Failure modes (Nygard)

| Failure | Verb response |
|---|---|
| Driver `REFUSAL` (Spec 147) | typed failure; emit a Reflection scoped to the failed concept; never retry the SAME prompt |
| Driver `RATE_LIMITED` mid-iteration | pause + backoff (driver-owned); the iteration counter is preserved |
| All `max_iterations` exhausted with gate failures | return `LyricResult` with `gate_verdicts` carrying the last failures; caller decides |
| `[anthropic]` extra missing | typed degraded result — scaffold returned with `driver_usage = TokenUsage.zero()` |
| Reflection write fails | typed failure; lyrics are NOT returned without provenance (rule 7) |
| Voice profile missing | typed `BAD_REQUEST{detail:"voice_profile_unknown"}` BEFORE the driver call (zero spend) |

## Interconnects

- **LLM-driver chain** (147) · **output-budget** (146) · **dogfood** (150).
- The lyrics analog of the novel scene-writer (Spec 130).
- Spec 206 (produce-album walk) drives this as the lyrics phase.
- Spec 213 (judged gates) augments the decidable gate verdicts with
  optional `judge=True` findings that feed the next iteration.
- Spec 216 (shared name-exposure gate) runs against generated lyrics
  the same way it runs against the promo draft.

## Open questions

1. One-shot or iterate-to-gate? **Recommend**: iterate — generate,
   run gates, regenerate on fail (bounded retries), like the novel loop.
2. Should the failing-gate hints be raw or summarised before re-prompting?
   **Recommend**: structured (gate name + line number + finding) so the
   Driver can target the fix; raw is cheap but noisy.
3. Where does the voice profile live? **Recommend**: a graph node typed
   `VoiceProfile` — already on Spec 095's surface; this verb only reads.
