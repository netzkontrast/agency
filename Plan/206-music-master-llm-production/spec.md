---
spec_id: "206"
slug: music-master-llm-production
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "093"
depends_on: ["093", "147", "150", "203"]
vision_goals: [4, 8]
affects:
  - agency/capabilities/music/_main.py
  - tests/test_music_master_llm.py
---

# Spec 206 — music master: LLM-production walkable

## Why

Spec 093 is the music-complete-port master — ~97 verbs across 7
clusters, full provenance moat on the pipeline. The pipeline is
DECIDABLE end to end (state, gates, catalogue) but the creative steps
(concept → lyrics → style prompt → promo) are where an LLM driver adds
the most value. The master should gain a top-level `produce-album`
walkable that drives the whole pipeline, dispatching the creative steps
to the Spec 147 Driver and the decidable steps to the existing verbs.

## Done When

- [ ] **`produce-album` walkable skill** chains the 7 clusters
      (lifecycle → lyrics → audio → catalogue → promo → research →
      gates), creative phases via Spec 147, decidable phases via the
      shipped verbs, each phase a hard gate where reversibility drops.
- [ ] **The provenance moat lights end to end** (Spec 093's E2E test
      extended with the LLM phases mocked).
- [ ] **Graph-query (Spec 203) answers "every asset SERVING this
      album + its gate"** — the music moat made queryable.
- [ ] Test: the walk drives the pipeline (mocked Driver); moat query
      returns the full chain.
- [ ] TODO row + drift clean.

## Interconnects

- **LLM-driver chain** (147) · **dogfood-loop** (150) ·
  Spec 203 (graph query) for the music moat.

## Open questions

1. One mega-walk or compose cluster walks? **Recommend**: compose —
   each cluster already has its skill; `produce-album` orchestrates.
