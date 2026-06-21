---
spec_id: "206"
slug: music-master-llm-production
status: draft
state: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "093"
depends_on: ["093", "147", "150", "203", "146", "207", "208", "213"]
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
      Typed return: `WalkResult = {intent_id, phases_completed: list[str],
      gates_passed: list[GateVerdict], artefacts_produced: list[ArtefactRef],
      driver_calls: int, total_tokens: int}`.
- [ ] **The provenance moat lights end to end** (Spec 093's E2E test
      extended with the LLM phases mocked).
- [ ] **Graph-query (Spec 203) answers "every asset SERVING this
      album + its gate"** — the music moat made queryable.

## Measurable invariants (relationships, not pinned counts)

- **Cluster coverage** — `len(set(WalkResult.phases_completed)) ==
  len(MUSIC_CLUSTERS)` (derived from `agency.capabilities.music.clusters`,
  not pinned at 7).
- **Provenance density** — `len(artefacts_produced) >=
  len(phases_completed)` (every phase emits at least one Artefact SERVES
  the album intent).
- **Gate non-skip** — `every cluster with a shipped gate verb appears in
  gates_passed` (computed from the registry; if a new gate verb lands, the
  walk must include it or the test fails).
- **Driver-call locality** — `driver_calls` counts ONLY the creative
  phases (lyrics/promo/judged gates); decidable phases must not invoke
  the Driver. Invariant: `driver_calls <= len(CREATIVE_CLUSTERS)`.

## Worked example (Given/When/Then)

```text
Given:  album_id created via lifecycle.new_album, [anthropic] extra
        installed, AnthropicDriver mocked to return gate-passing payloads
When:   skill_walk(intent_id, "produce-album", {album_id})
Then:   returns WalkResult with phases_completed ⊇ MUSIC_CLUSTERS
        AND artefacts_produced contains ≥1 ArtefactRef per cluster
        AND analyze.graph_query("assets SERVING album_id") returns the
        full chain (lyrics → audio → master → promo → catalogue entry)
        AND every Reflection emitted carries the album_id in scope
```

## Failure modes (Nygard)

| Failure | Walk response |
|---|---|
| Driver `REFUSAL` on lyrics (Spec 147) | mark phase failed; surface to walker; never silently skip downstream gates |
| Driver `RATE_LIMITED` mid-walk | pause walk; emit `MonitorEvent("walk_paused")`; resume from last completed phase |
| Decidable gate fails (e.g. explicit-checker) | walk halts at that phase; partial WalkResult returned; no downstream creative dispatch |
| Managed-Agent audio driver (Spec 209) timeout | fall back to FakeAudioDriver if `xcap` flag set; else typed failure |
| Reflection write fails (graph offline) | typed failure; walk does NOT proceed (provenance moat is non-negotiable) |

## Interconnects

- **LLM-driver chain** (147) · **dogfood-loop** (150) ·
  Spec 203 (graph query) for the music moat.
- Spec 146 (output-prefix) — the walk's per-phase payloads honor the
  frozen-prefix envelope.
- Spec 207 (lifecycle budget) — the lifecycle phase's list outputs
  capture-and-recall under the same walk.
- Spec 208 (lyrics LLM) + Spec 211 (promo LLM) + Spec 213 (judged gates)
  are the creative-phase consumers.
- Spec 209 (Managed-Agent audio) — fallback driver when local DSP absent.

## Open questions

1. One mega-walk or compose cluster walks? **Recommend**: compose —
   each cluster already has its skill; `produce-album` orchestrates
   via `develop.skill_walk` so each phase stays bounded-context.
2. Resume semantics on driver failure? **Recommend**: resume from the
   last completed phase via the intent_id checkpoint (Spec 093's
   lifecycle state IS the resume marker); never restart the pipeline.
3. Where does `produce-album` declare its cluster order? **Recommend**:
   derive from the cluster registry's `depends_on` ordering — never
   hand-pin the order (CLAUDE.md rule 8).
