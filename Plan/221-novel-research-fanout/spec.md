---
spec_id: "221"
slug: novel-research-fanout
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "105"
depends_on: ["105", "180", "126", "168"]
vision_goals: [8, 1]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_novel_research_fanout.py
---

# Spec 221 — novel research fan-out + ingest reuse

## Why

Spec 105 (novel-research) ships the research surface for a novel
(worldbuilding facts, period detail, technical accuracy). It delegates
to `agency.research`, which is gaining Managed-Agent fan-out (Spec 180)
+ server-side web (Spec 168) + the large-corpus ingest (Spec 126, the
KP example). Novel research should inherit all three: a historical-novel
fact-check can fan out, and a large source corpus ingests
subagent-isolated (the KP pattern, proven).

## Done When

- [ ] **Novel research inherits Spec 180 fan-out + Spec 168 web depth +
      Spec 126 ingest** — no novel-specific LLM code (the 105 delegation
      pattern, validated).
- [ ] **Ingested sources link to the novel** (the KP `ingested-source`
      Artefact pattern) as research provenance.
- [ ] **Citations flow into the codex** (Spec 132) as entity sources.
- [ ] Test: a novel research call uses the upgraded path (mocked);
      ingest links to the novel.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 180 (fan-out) + Spec 168 (web) + Spec 126 (ingest) inherited.
- Spec 132 (codex) consumes the citations.

## Open questions

1. Novel-specific specialist roles? **Recommend**: reuse shared roles;
   a `period-accuracy` specialist is a Slice-2 if demand appears.
