---
spec_id: "236"
slug: research-ingest-corpus-management
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "126"
depends_on: ["126", "228", "203", "168"]
vision_goals: [1, 2]
affects:
  - agency/capabilities/research/_main.py
  - tests/test_research_ingest_corpus.py
---

# Spec 236 — ingest corpus management (lifecycle + dedup + query)

## Why

Spec 126 ships `research.ingest_gdoc` + `record_ingested_source` —
subagent-isolated single-source ingest, idempotent on `(intent_id,
sha256)`. As corpora grow (the KP proof set was 6 docs; a dossier
corpus could be 60), we need CORPUS-level operations: list, deduplicate,
re-ingest with diff, query across corpus. The Spec 228 dossier cap
needs these. Adds bulk ingest with progress streaming via Spec 021.

## Done When

- [ ] **`ingest_corpus(sources, dest) -> CorpusIngestResult`** where
      `CorpusIngestResult = {ingested: list[SourceId], skipped:
      list[(SourceId, reason)], duplicates_collapsed: int,
      total_bytes: int, elapsed_ms: int}` — bulk variant with progress
      events (Spec 021 MonitorEvents per source). Invariant:
      `len(ingested) + len(skipped) == len(sources)` AND
      `total_bytes == sum(s.bytes for s in ingested)`.
- [ ] **`list_corpus(intent_id) -> list[Source]` + `dedup_corpus(intent_id)
      -> DedupResult`** lifecycle verbs. Invariant: after `dedup_corpus`,
      no two Source nodes share the same `sha256` within the intent
      scope (the (intent_id, sha256) uniqueness from Spec 126 extends
      to retro-dedup).
- [ ] **Idempotency relation, not pinned count** — invariant: re-running
      `ingest_corpus` on the same sources produces `ingested == []` and
      `duplicates_collapsed == len(sources)`; never a fresh write.
- [ ] **Cross-corpus graph queries** via Spec 203 — "every claim citing
      ≥2 sources". Invariant: the query returns a relation `{claim_id:
      list[SourceId]}` where every list has `len >= 2`.
- [ ] **Server-side web fetch** (Spec 168) extends ingest to URL sources.
- [ ] **Failure modes** — URL fetch 4xx/5xx → source skipped with
      `Codes.FETCH_FAILED` + HTTP status; PDF parse error →
      `Codes.PARSE_FAILED` + page number; sha256 mismatch on re-fetch
      (URL content changed) → ingested as a NEW source with a
      `SUPERSEDES` edge to the old one (provenance preserved); progress
      event channel disconnect (Spec 021) → ingest continues, events
      buffered for late subscribers.
- [ ] Test: bulk ingest reports progress; dedup collapses duplicates;
      cross-query returns claims.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  a corpus of 6 sources (4 unique sha256s, 2 dupes of existing)
When:   ingest_corpus(sources, dest=intent_id) runs
Then:   CorpusIngestResult.ingested has 4 items AND
        duplicates_collapsed == 2 AND
        total_bytes == sum of the 4 unique source byte counts AND
        a MonitorEvent fires per source (6 events total)

Given:  the same corpus re-ingested
When:   ingest_corpus(sources, dest=intent_id) runs again
Then:   CorpusIngestResult.ingested == [] AND
        duplicates_collapsed == 6 AND no new Source nodes were created
```

## Interconnects

- Spec 228 (dossier) is the primary consumer.
- Spec 203 (graph query) for cross-corpus relational answers.
- Spec 235 (typed paths) — claim→CITES→Source traversal underlies the
  ≥2-source cross-query.
- Spec 234 (format-driver) — corpus exports share sha256 hygiene.
- Spec 240 (scene-writer loop) — research corpus feeds the brief
  assembly with cited claims.

## Open questions

1. **Dedup scope.** Within an intent only, or cross-intent? **Recommend:**
   within intent — cross-intent dedup conflates research contexts.
2. **URL re-fetch policy.** **Recommend:** cache 7 days; re-fetch on
   request, emit SUPERSEDES when sha256 differs.
3. **Concurrency.** Sequential ingest or parallel per-source?
   **Recommend:** parallel with worker cap = 4 (server-side fetch
   politeness); progress events still ordered per-source completion.
