---
spec_id: "216"
slug: music-name-exposure-driver
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "119"
depends_on: ["119", "147", "138", "208"]
vision_goals: [4]
affects:
  - agency/capabilities/music/_main.py
  - tests/test_music_name_exposure_driver.py
---

# Spec 216 — music name-exposure: fuzzy + cross-domain reuse

## Why

Spec 119 (music-name-exposure) ships whole-word + case-insensitive
blocklist scanning ("Lex" never fires inside "lexicon") across lyrics +
promo. It is purely decidable — a name spelled slightly differently
(homophone, misspelling, split-across-lines) slips through. The novel
plural-character system (Spec 138) has the SAME need
(`check_alter_recognition` — names never labeled). This generalizes the
name-exposure check into a shared substrate both domains use, with an
optional Spec 147 fuzzy pass for near-misses.

## Done When

- [ ] **The name-exposure check is extracted to a shared substrate**
      both music (119) and novel (138) consume — one implementation, two
      callers (the drop-in bar, CLAUDE.md).
- [ ] **Optional fuzzy pass** — the Spec 147 Driver flags near-miss
      exposures (homophones, split names) the decidable scan misses;
      tagged `judged`, advisory.
- [ ] **The decidable whole-word scan stays the hard gate** (Spec 119).
- [ ] Test: a homophone leak is fuzzy-flagged (mocked); the decidable
      gate unchanged; novel + music both call the shared check.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 138 (alter recognition) is the cross-domain co-consumer.
- **LLM-driver chain** (147) for the fuzzy pass.
- Spec 208 (lyrics generation) runs the gate on generated text.

## Open questions

1. Where does the shared check live? **Recommend**: a substrate helper
   (like `ctx.neighbors`) since two domains need it — or a tiny
   `text` capability if a third consumer appears.
