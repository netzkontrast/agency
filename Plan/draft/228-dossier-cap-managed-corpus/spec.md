---
spec_id: "228"
slug: dossier-cap-managed-corpus
status: draft
state: draft
last_updated: 2026-06-11
owner: "@agency"
enhances: "112"
depends_on: ["112", "126", "180", "203", "147", "150", "146", "149", "221", "212"]
vision_goals: [4, 1, 2]
affects:
  - agency/capabilities/dossier/  (when shipped)
  - tests/test_dossier_managed_corpus.py
---

# Spec 228 — dossier capability: managed corpus + ingest

## Why

Spec 112 (dossier-capability) is the research-brief authoring + corpus
management + entity ontology surface — "feeds INTO research cap; novel
is first consumer; reusable by music/screenplay/journalism/legal/
academic". A dossier's corpus is exactly what the large-corpus ingest
(Spec 126, the KP example) + Managed-Agent fan-out (Spec 180) serve:
ingest a big source set subagent-isolated, fan out the analysis, and
query the resulting entity graph relationally (Spec 203). Without this
enhancement, every consumer (novel/music/journalism) would re-implement
its own corpus → entity pipeline, defeating the reusability premise.

## Done When

- [ ] **Dossier corpus management uses Spec 126 ingest** with a typed
      return shape:
      ```python
      DossierIngestResult = {
        "dossier_id":      str,
        "sources_ingested": int,
        "bytes_isolated":   int,        # body never crossed to orchestrator
        "entities_extracted": int,
        "subagent_id":     str,         # Spec 180 handle
        "tokens_returned":  int,        # the summary that DID cross
        "tokens_isolated":  int,        # what stayed in the subagent
      }
      ```
      Invariant: `tokens_returned < tokens_isolated * 0.1` — the body
      never crosses; only a structured summary does. This is the KP
      pattern made testable.
- [ ] **Dossier analysis fans out** (Spec 180) when corpus exceeds a
      configured threshold (default: 50K tokens total or ≥ 20 sources).
      Each fan-out shard returns a typed `EntityShard` that the
      orchestrator merges; no shard's raw body crosses.
- [ ] **The entity ontology is graph-query-able** (Spec 203):
      ```python
      EntityQuery = {
        "min_source_count": int,        # "≥ N sources mention this"
        "entity_type":      str | None,
        "time_window":      tuple[str, str] | None,
      }
      EntityResult = {
        "entity_id":   str,
        "label":       str,
        "source_ids":  list[str],       # citations preserved
        "first_seen":  str,             # bi-temporal
        "confidence":  float,
      }
      ```
      Invariant: every returned `EntityResult.source_ids` resolves to a
      live source node — no dangling citations.
- [ ] **The dossier is reusable** — novel (Spec 221) + music (Spec 212)
      research both consume the SAME `dossier.query_entities(...)` verb;
      neither re-implements entity extraction. Parity test asserts the
      same fixture corpus yields the same entity graph for both consumers.
- [ ] **Failure modes** (touches LLM-driven extraction + subagent fan-out):
      `Codes.INGEST_OVERFLOW` when a single source exceeds the subagent
      budget (rejected with citation, not silently truncated);
      `Codes.SUBAGENT_REFUSAL` propagated from Spec 147 (the wrapping
      verb degrades to citation-only mode);
      `Codes.ENTITY_PARSE_FAILED` when the structured-output schema
      mismatches (degrade to keyword extraction, emit Reflection);
      `Codes.CITATION_DANGLING` when a merged shard references a source
      no longer in the corpus (hard error — corpus integrity).
- [ ] **Output-budget honored** (Spec 146) — dossier summaries carry a
      `cache_safe_prefix_tokens` field; the prefix is the corpus
      manifest (byte-stable per dossier_id), the tail is the query result.
- [ ] **Score-reflection edge** — every entity extraction emits a
      `Reflection(scope="dossier-entity")` consumable by Spec 150's
      classifier; entity-merge conflicts become amendment proposals.
- [ ] **112 row flips toward Shipped** with derived completion %
      (Spec 149 reads the verb count off the live registry).
- [ ] Test: a 100-source corpus ingests + fans out (mocked); entity
      query returns the expected subgraph; the body-isolation
      invariant (`tokens_returned < tokens_isolated * 0.1`) holds;
      novel + music consumers return byte-identical entity graphs on
      a fixture corpus.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  60 sources totaling 200K tokens for dossier "kp-album"
When:   dossier.ingest(dossier_id="kp-album", sources=[...])
Then:   returns DossierIngestResult with sources_ingested == 60,
        bytes_isolated > 0, tokens_returned < tokens_isolated * 0.1,
        subagent_id resolvable; orchestrator context cost ~ summary only

Given:  the ingested dossier and "≥ 3 sources mention this entity"
When:   dossier.query_entities(EntityQuery(min_source_count=3))
Then:   returns EntityResult list; every entity's source_ids
        contains ≥ 3 live source nodes; no dangling citations;
        result is graph-query-able by Spec 203 directly

Given:  a source exceeds the subagent budget (single 80K-token PDF)
When:   ingest runs
Then:   raises Codes.INGEST_OVERFLOW with the source citation,
        the rest of the corpus ingests cleanly,
        a Reflection(scope="ingest-overflow") is emitted for Spec 150

Given:  novel cap (Spec 221) and music cap (Spec 212) both consume
        the same dossier
When:   each calls dossier.query_entities(EntityQuery(min_source_count=2))
Then:   returns byte-identical EntityResult lists (reusability parity)
```

## Failure modes (Nygard)

| Failure | Response |
|---|---|
| `INGEST_OVERFLOW` | reject source with citation; corpus partial-ingests; Reflection emitted |
| `SUBAGENT_REFUSAL` | degrade to citation-only summary; never silent zero |
| `ENTITY_PARSE_FAILED` | fall back to keyword extraction; confidence == 0.3 |
| `CITATION_DANGLING` | hard error; rollback merge; corpus integrity is load-bearing |
| Subagent timeout | partial-result return with `completed_shards` count |
| Cross-consumer drift | parity test fails; novel/music must converge before ship |

## Interconnects

- Spec 126 (large-corpus ingest) is the subagent-isolation pattern.
- Spec 180 (Managed-Agent fan-out) is the analysis substrate.
- Spec 203 (graph-query) is how downstream verbs read the entity graph.
- Spec 147 (LLM driver) does the structured entity extraction.
- Spec 146 (output-budget) governs the summary that crosses back.
- Spec 150 (dogfood loop) sees entity-merge conflicts as amendments.
- Spec 149 (derived docs) reads verb count for the 112 row.
- Spec 221 (novel research) is the first consumer.
- Spec 212 (music research) is the second consumer — proves reusability.

## Open questions

1. Ship dossier cap first or enhance-in-place? **Recommend**: ship the
   112 Slice 1 first (the bare corpus + entity surface), then this
   enhancement layers the subagent/fan-out wiring. Sequencing noted
   in 112's plan.
2. **Body-isolation threshold.** When does a corpus warrant subagent
   fan-out vs. inline? **Recommend**: 50K tokens total OR ≥ 20 sources;
   the threshold is a documented tunable (rule 8 — named config, not
   magic number), overridable per call.
3. **Entity-merge strategy across shards.** Exact-match, fuzzy, or
   LLM-mediated? **Recommend**: exact + canonicalized (lowercase,
   stripped); LLM-mediated merge defers to Slice 2 once
   `entity_parse_failed` rate drops below 5%.
4. **Citation freshness on source-mutation.** If a source updates, do
   existing entities re-resolve? **Recommend**: bi-temporal — the entity
   keeps the `first_seen` reference; a re-ingest creates a new entity
   version, never mutates the old one (matches the substrate's
   bi-temporal discipline).
