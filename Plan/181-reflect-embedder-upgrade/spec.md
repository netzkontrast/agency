---
spec_id: "181"
slug: reflect-embedder-upgrade
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "045"
depends_on: ["045", "147", "150", "082"]
vision_goals: [2, 6]
affects:
  - agency/capabilities/reflect/_embed.py
  - tests/test_reflect_embedder_upgrade.py
---

# Spec 181 — reflect embedder upgrade (Anthropic embeddings boundary)

## Why

Spec 045 ships `reflect.recall_semantic` with a pluggable TF-IDF/BGE
embedder boundary. The dogfood loop (Spec 150) leans hard on
recall_semantic to select candidate Reflections for the amendment
classifier — so recall QUALITY directly bounds loop quality. When an
embeddings backend is available (the boundary already exists), wiring a
higher-quality embedder lifts the whole loop, and the boundary keeps the
TF-IDF default for zero-config.

## Done When

- [ ] **A high-quality embedder option** added behind the existing
      Spec 045 boundary (no new boundary — extend the pluggable one).
- [ ] **`reflect.recall_semantic` quality benchmark** — a fixture of
      query→expected-Reflection pairs; assert the upgraded embedder ≥
      TF-IDF baseline recall@k.
- [ ] **Zero-config TF-IDF default preserved** (Spec 045); the upgrade
      activates only when its dep/extra is present (`agency_doctor`
      reports the live backend — Spec 170).
- [ ] **Spec 150's candidate selection uses the best available
      embedder** automatically.
- [ ] Test: recall@k improves on the fixture with the upgraded backend;
      TF-IDF fallback deterministic.
- [ ] TODO row + drift clean.

## Interconnects

- **Dogfood-loop chain** (150): recall quality bounds loop quality.
- Spec 045 (semantic recall) is the boundary; Spec 170 (doctor)
  reports the backend.

## Open questions

1. Which embedder? **Recommend**: keep BGE as the local option; add an
   API-embeddings option behind `[anthropic]` only if measured recall
   justifies the call cost.
