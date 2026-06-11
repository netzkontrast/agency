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
      The recall call returns a typed shape:
      ```python
      RecallResult = {
        "matches":       list[ReflectionMatch],
        "backend":       Literal["tfidf","bge","anthropic"],
        "k":             int,
        "fallback_used": bool,                # backend downgraded?
        "embed_ms":      int,                 # latency budget signal
      }
      ReflectionMatch = {
        "reflection_id": str,
        "score":         float,               # backend-normalized 0..1
        "scope":         str,
      }
      ```
- [ ] **Invariant — recall lift, not pinned count.** On a query→expected
      fixture, `recall@k(upgraded) ≥ recall@k(tfidf) + epsilon` where
      `epsilon ≥ 0.05` (relative lift, not a magic number). Assert
      the RELATIONSHIP, never freeze the absolute value.
- [ ] **Invariant — zero-config default preserved.** With the upgrade
      extra absent, `RecallResult.backend == "tfidf"` and the result
      is byte-identical to the Spec 045 baseline on a frozen fixture.
- [ ] **Invariant — degradation is observable.** When the upgraded
      backend fails (network, dep, quota), `fallback_used=True` and
      `backend` reports the actual backend used — never silently
      misreport. `agency_doctor` (Spec 170) shows the live backend.
- [ ] **Invariant — loop coupling.** Spec 150's candidate-Reflection
      selection calls `reflect.recall_semantic` once per amendment
      proposal; assert the call site uses no hardcoded backend
      (it discovers the live one).
- [ ] **Bounded latency.** `embed_ms ≤ embed_latency_budget_ms`
      (documented config, default 2000); over-budget runs warn but do
      not fail.
- [ ] Test: recall@k improves on the fixture with the upgraded backend;
      TF-IDF fallback deterministic; fallback_used flag observable.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  a Reflection corpus with 200 entries + a 20-pair query→expected
        fixture; both BGE and TF-IDF available
When:   reflect.recall_semantic(query="abstraction over single caller",
                                 k=5, backend="auto")
Then:   returns RecallResult{
            backend: "bge",
            matches: [5 ReflectionMatch entries, top score 0.83],
            fallback_used: False,
            embed_ms: 340
        }
        AND recall@5(bge) ≥ recall@5(tfidf) + 0.05 on the fixture
        AND with backend="bge" extra UNINSTALLED, a re-run returns
            backend="tfidf", fallback_used=True, no exception raised
        AND agency_doctor reports backend="tfidf" in the downgraded run
```

## Failure modes (Nygard)

| Failure | Recall response |
|---|---|
| Upgrade extra missing | `backend="tfidf"`, `fallback_used=True`; emit Reflection(`scope="embedder-downgrade"`) once per session |
| API embeddings quota exhausted | fall back to BGE (or TF-IDF); record `fallback_used=True`; do not raise |
| Embedder model file corrupt | typed `Codes.EMBEDDER_LOAD_FAILED`; fall through to TF-IDF; doctor reports the failure |
| Latency budget breached | warn, return matches; Spec 150 records the regression for the loop |
| Recall lift regression on fixture (new model worse than TF-IDF) | CI test fails — block the upgrade until rectified |

## Interconnects

- **Dogfood-loop chain** (150): recall quality bounds loop quality;
  amendment proposals depend on candidate selection.
- **LLM-driver chain** (147): the API-embeddings option (if shipped)
  shares the driver envelope and `Usage` accounting.
- Spec 045 (semantic recall) is the pluggable boundary — extend, not
  replace.
- Spec 170 (doctor) reports the live backend + fallback state.
- Spec 082 (reflect filter/dedup) shares the corpus; assert the
  embedder runs on the deduplicated set, not the raw stream.
- Spec 178 (analyze judge axis) feeds Reflections this surface
  recalls; the loop closes through here.
- Spec 183 (intent-chain opportunity detector) uses recall to find
  prior proposals before emitting duplicates.

## Open questions

1. **Which embedder?** **Recommend**: keep BGE as the local default
   upgrade option (no API call cost, deterministic); add an
   API-embeddings option behind `[anthropic]` ONLY if measured recall
   lift on the fixture justifies the per-call cost.
2. **Re-embed on corpus growth?** **Recommend**: lazy — embed on
   first recall, cache by `reflection_id` + embedder version; bulk
   re-embed only on embedder version bump.
3. **Score normalization across backends?** **Recommend**: backend
   reports raw cosine; recall layer min-max normalizes per query for
   comparability. Document the normalization in the typed shape so
   downstream Spec 150 thresholds are backend-agnostic.
