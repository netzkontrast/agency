---
spec_id: "179"
slug: document-render-llm-narrative
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "043"
depends_on: ["043", "147", "146", "154"]
vision_goals: [7, 1]
affects:
  - agency/capabilities/document/_main.py
  - tests/test_document_narrative.py
---

# Spec 179 — document.render narrative scope (composition + optional LLM)

## Why

Spec 043 ships `render` (4 graph→md scopes) + `explain` (composition,
not generation) + `index_repo` (94% token reduction). `explain` is
deliberately composition-only. But a `research-report` scope (named as
a Spec 044 v2 followup) and an audit-narrative scope want an optional
LLM pass that WEAVES the composed facts into prose — strictly on top of
the graph-derived skeleton (Goal 7: the graph is the store, prose is the
rendered view), never inventing facts.

## Done When

- [ ] **`document.render(scope="research-report")`** composes the
      graph skeleton (Citations, claims, evidence) then optionally runs
      the Spec 147 Driver to narrate — every sentence traceable to a
      composed node (no free invention; a lint asserts coverage).
- [ ] **The skeleton is the cache-stable prefix** (Spec 146); the
      narrated body recalls via Spec 154 when large.
- [ ] **Degrades to composition-only** without `[anthropic]` (Spec 043
      behavior preserved).
- [ ] Test: report renders from a fixture graph; every narrated claim
      maps to a node; composition-only fallback deterministic.
- [ ] TODO row + drift clean.

## Interconnects

- **LLM-driver chain** (147) · **output-budget chain** (146/154).
- Spec 044 (research) is the first consumer (research-report scope).

## Open questions

1. How to enforce "no invention"? **Recommend**: post-render coverage
   check — every noun-phrase claim must trace to a composed node id;
   uncovered claims flag (not auto-strip).
