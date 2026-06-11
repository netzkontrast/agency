---
spec_id: "241"
slug: character-knowledge-llm-extract
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "131"
depends_on: ["131", "147", "150", "146"]
vision_goals: [4, 2]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_character_knowledge_extract.py
---

# Spec 241 — character-knowledge LLM extract on scene-integrate

## Why

Spec 131 ships KnownFact + 3 verbs; the author calls
`record_character_learns` manually after writing a scene. When the
scene-writer integrates (Spec 130 phase 5) the Driver should
auto-extract candidate KnownFacts and propose them — author confirms,
the loop is closed. Spec 130's Followup explicitly names "auto-update
LEARNED_IN ledger on phase 5" as Slice 2.

## Done When

- [ ] **`novel.extract_facts_from_scene(scene_id) -> ExtractResult`**
      where `ExtractResult = {scene_id, proposed: list[KnownFactDraft],
      rejected: list[(draft, reason)], driver_tokens: int}` and
      `KnownFactDraft = {character_id, fact, learned_at_beat,
      confidence: float, source_locus}`. Runs the Spec 147 Driver with
      `output_config.format` (a strict KnownFact schema). Invariant:
      `len(proposed) + len(rejected) == driver_proposed_count`.
- [ ] **Proposed facts land as `canon_status=proposal`** (Spec 137) —
      invariant: NO KnownFact exits this verb as `canon`; the author
      MUST call `confirm_known_fact(id)` to promote. Asserted:
      `all(f.canon_status == "proposal" for f in proposed)`.
- [ ] **Scene-writer phase 5 chains it** (130 Slice 2 closed) —
      invariant: phase 5 output IS the ExtractResult; the walk never
      auto-confirms, only surfaces for review.
- [ ] **Anachronism check (Spec 131)** runs against proposals before
      they canonize — invariant: any draft where
      `learned_at_beat PRECEDES scene.beat_id` is automatically rejected
      with `Codes.ANACHRONISTIC_FACT`; the draft never lands as
      proposal.
- [ ] **Confidence relation, not threshold-pinned** — invariant: drafts
      with `confidence < 0.5` go to `rejected` with reason
      `low_confidence`; the threshold is configurable via
      `NovelConfig.extract_confidence_floor`, never a magic constant
      in the verb body.
- [ ] **Byte-stable prompt prefix** (Spec 146) — invariant: extract
      prompt prefix depends only on the scene's brief shape (Spec 237),
      not on the in-flight extraction set. Two runs on the same scene
      hit identical cache keys.
- [ ] **Failure modes** — Driver unreachable (Spec 147) →
      `Codes.DRIVER_UNAVAILABLE`, `proposed=[]`, scene-writer phase 5
      becomes a no-op (gate doesn't block); malformed JSON from Driver
      → `Codes.EXTRACT_PARSE_FAILED`, draft skipped, others retained;
      character_id unknown in scene → draft rejected with
      `Codes.UNKNOWN_CHARACTER` (typo in Driver output).
- [ ] Test: integration extracts ≥1 fact from a fixture scene (mocked).
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  scene S where character C learns that the antagonist's name is
        "Vey"; mocked Driver returns 3 candidate facts:
          (C, "name is Vey", beat_id=S.beat, confidence=0.9, "p2 l3"),
          (C, "fears spiders", beat_id=S.beat, confidence=0.4, "p4 l1"),
          (C, "knows the code", beat_id=EARLIER_BEAT, confidence=0.8, "p1")
When:   extract_facts_from_scene(S) runs
Then:   len(result.proposed) == 1 (the name-is-Vey fact) AND
        len(result.rejected) == 2 AND
        rejection reasons == ["low_confidence","anachronistic_fact"] AND
        the proposed fact has canon_status == "proposal" AND
        no fact is auto-canonized

Given:  the author calls confirm_known_fact on the proposed fact
When:   the canonization runs
Then:   the fact lands canon_status == "canon" AND a CONFIRMED_BY edge
        is recorded for provenance
```

## Failure modes

LLM/remote/cache surfaces: Driver returns plausible-but-wrong character
attribution (the fact is real but for the wrong character) — handled by
the anachronism check + author review; cache poisoning across scenes
prevented by per-scene cache key (Spec 237); rate-limit on Driver →
return partial `proposed` list with `Codes.DRIVER_RATE_LIMITED` warn,
never lose state.

## Interconnects

- **LLM-driver chain** (147) · **Dogfood-loop** (150) — extractions
  feed amendment proposals when patterns recur.
- Spec 137 (canon-status) — never silent canon (the [V] discipline).
- Spec 237 (scene-brief cache) — extract prompt shares the brief
  prefix for cache amortization.
- Spec 240 (scene-writer loop) — phase 5 of the iterate-to-gate walk.
- Spec 238 (story-time query) — anachronism check uses PRECEDES paths.
- Spec 242 (codex fuzzy match) — character_id resolution shares the
  whole-word/fuzzy substrate (Spec 216).

## Open questions

1. **Extraction window.** Only the integrated scene body, or include
   prior scenes for context? **Recommend:** scene body only; prior
   context bloats the prefix and is already in the brief.
2. **Confirmation UX.** Auto-confirm high-confidence (>0.95)?
   **Recommend:** no — the [V] discipline (Spec 137) is the moat;
   never silent canon, regardless of confidence.
3. **De-duplication.** Same fact extracted across multiple scenes?
   **Recommend:** dedupe by `(character_id, fact_signature)`; the
   second occurrence records a LEARNED_AGAIN edge for provenance,
   not a new fact.
