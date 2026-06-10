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

- [ ] **`ingest_corpus(sources, dest)`** — bulk variant with progress
      events (Spec 021 MonitorEvents per source).
- [ ] **`list_corpus(intent_id)` + `dedup_corpus`** lifecycle verbs.
- [ ] **Cross-corpus graph queries** via Spec 203 — "every claim citing
      ≥2 sources".
- [ ] **Server-side web fetch** (Spec 168) extends ingest to URL sources.
- [ ] Test: bulk ingest reports progress; dedup collapses duplicates;
      cross-query returns claims.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 228 (dossier) is the primary consumer.
- Spec 203 (graph query) for cross-corpus relational answers.
