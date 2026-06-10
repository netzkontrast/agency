---
spec_id: "211"
slug: music-promo-llm-copy
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "098"
depends_on: ["098", "147", "119", "150"]
vision_goals: [4, 1]
affects:
  - agency/capabilities/music/_main.py
  - tests/test_music_promo_llm.py
---

# Spec 211 — music promo LLM copy generation

## Why

Spec 098 (music-promo) ships 8 verbs for platform-specific promo +
`promo_review` (which Spec 119 extended with name-exposure scanning).
Like lyrics (Spec 208), the actual COPY is written in chat. The agency
port should make `write_promo(platform)` a verb: the Spec 147 Driver
drafts platform-tuned copy from the album themes + track concepts, and
the shipped `promo_review` + name-exposure gates (Spec 119) validate it.

## Done When

- [ ] **`write_promo(album_id, platform)`** drives the Spec 147 Driver
      with album themes + the platform template; output runs through the
      shipped `promo_review` + name-exposure gate (Spec 119).
- [ ] **Name-exposure (Spec 119) blocks** a generated post that leaks a
      blocklisted name — the gate is non-negotiable.
- [ ] **Generation honors the output budget** (Spec 146); drafts record
      Reflections (Spec 150).
- [ ] **Degrades** to the template scaffold without `[anthropic]`.
- [ ] Test: generated copy passes review; a name leak blocks (mocked
      Driver).
- [ ] TODO row + drift clean.

## Interconnects

- **LLM-driver chain** (147) · **dogfood** (150).
- Spec 119 (name-exposure) is the hard gate on generated copy.

## Open questions

1. Per-platform or one draft adapted? **Recommend**: per-platform (the
   templates differ); shared theme prefix is cache-stable (Spec 146).
