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

- [ ] **`novel.extract_facts_from_scene(scene_id)`** runs the Spec 147
      Driver with `output_config.format` (a strict KnownFact schema) to
      propose facts from the integrated body.
- [ ] **Proposed facts land as `canon_status=proposal`** (Spec 137) —
      never silent canon; author confirms.
- [ ] **Scene-writer phase 5 chains it** (130 Slice 2 closed).
- [ ] **Anachronism check (Spec 131)** runs against proposals before
      they canonize.
- [ ] Test: integration extracts ≥1 fact from a fixture scene (mocked).
- [ ] TODO row + drift clean.

## Interconnects

- **LLM-driver chain** (147) · **Dogfood-loop** (150) — extractions
  feed amendment proposals when patterns recur.
- Spec 137 (canon-status) — never silent canon (the [V] discipline).
