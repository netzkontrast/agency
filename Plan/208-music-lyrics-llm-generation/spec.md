---
spec_id: "208"
slug: music-lyrics-llm-generation
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "095"
depends_on: ["095", "147", "146", "150"]
vision_goals: [4, 1]
affects:
  - agency/capabilities/music/_main.py
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

- [ ] **`write_lyrics(track_id, ...)`** drives the Spec 147 Driver with
      the track concept, the 095 templates, and the voice profile;
      returns lyrics the shipped gates (rhyme/prosody/explicit) validate.
- [ ] **Generation honors the output budget** (Spec 146) — the prompt
      prefix (templates) is cache-stable across tracks.
- [ ] **Drafts record provenance** + a Reflection (Spec 150) so lyric
      iterations feed the dogfood loop.
- [ ] **Degrades** without `[anthropic]` (returns the structured
      template scaffold, Spec 095 behavior).
- [ ] Test: `write_lyrics` returns gate-passing lyrics (mocked Driver).
- [ ] TODO row + drift clean.

## Interconnects

- **LLM-driver chain** (147) · **output-budget** (146) · **dogfood** (150).
- The lyrics analog of the novel scene-writer (Spec 130).

## Open questions

1. One-shot or iterate-to-gate? **Recommend**: iterate — generate,
   run gates, regenerate on fail (bounded retries), like the novel loop.
