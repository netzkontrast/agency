---
spec_id: "228"
slug: dossier-cap-managed-corpus
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "112"
depends_on: ["112", "126", "180", "203"]
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
query the resulting entity graph relationally (Spec 203).

## Done When

- [ ] **Dossier corpus management uses Spec 126 ingest** — large source
      sets ingest subagent-isolated; the body never crosses into the
      orchestrator (the proven KP pattern).
- [ ] **Dossier analysis fans out** (Spec 180) when the corpus is large.
- [ ] **The entity ontology is graph-query-able** (Spec 203) — "every
      entity mentioned in ≥3 sources" in one call.
- [ ] **The dossier is reusable** — novel (Spec 221) + music (Spec 212)
      research both consume it.
- [ ] Test: a corpus ingests + fans out (mocked); entity query returns
      the expected subgraph.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 126 (ingest) + Spec 180 (fan-out) + Spec 203 (graph query).
- Spec 221 (novel research) + Spec 212 (music research) are consumers.

## Open questions

1. Ship dossier cap first or enhance-in-place? **Recommend**: ship the
   112 Slice 1 first, then this enhancement — sequence noted in 112.
