---
spec_id: "217"
slug: novel-master-llm-build
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "101"
depends_on: ["101", "147", "145", "203"]
vision_goals: [4, 8]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_novel_master_llm.py
---

# Spec 217 — novel master: LLM-build walkable

## Why

Spec 101 is the novel-complete-build master. The downstream waves
(120-145) built a deep graph surface (storyform, prose, worldbuilding,
codex, KP features) but there is no top-level walkable that drives a
whole novel from premise to manuscript, dispatching the creative steps
to the Spec 147 Driver and the decidable steps to the shipped verbs.
The novel-preflight (Spec 145) is the per-scene gate; this is the
book-level orchestrator.

## Done When

- [ ] **`build-novel` walkable** chains premise → storyform → structure
      → worldbuilding → chapter-briefing → scene-writing → editorial →
      manuscript, creative phases via Spec 147, decidable via shipped
      verbs, hard gates where reversibility drops.
- [ ] **The novel provenance moat lights end to end** (a fixture novel,
      LLM phases mocked).
- [ ] **Graph-query (Spec 203) answers "every scene SERVING this novel
      + its storyform + its gate"** — the novel moat made queryable.
- [ ] Test: the walk drives the pipeline; moat query returns the chain.
- [ ] TODO row + drift clean.

## Interconnects

- **LLM-driver chain** (147) · Spec 145 (preflight) is the per-scene
  gate this composes · Spec 203 (graph query).

## Open questions

1. Mega-walk or compose? **Recommend**: compose the existing skills
   (scene-writer 130, preflight 145, editorial 122) — `build-novel`
   orchestrates them.
