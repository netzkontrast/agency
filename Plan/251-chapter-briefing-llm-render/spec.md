---
spec_id: "251"
slug: chapter-briefing-llm-render
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "141"
depends_on: ["141", "147", "237", "146"]
vision_goals: [4, 1]
affects:
  - agency/capabilities/novel/_main.py
  - tests/test_chapter_briefing_render.py
---

# Spec 251 — chapter briefing LLM-rendered template

## Why

Spec 141 ships ModeBlock + the 13-section vendored template +
`render_chapter_briefing` (aggregates the 136-140 stack). Template
fills are mechanical composition today. With Spec 147 the Driver can
fill the freeform sections (rationale, open-questions, callbacks) from
the chapter's graph context; aggregation stays decidable. And the
template is exactly the kind of cache-stable prefix Spec 237 anchors.

## Done When

- [ ] **`render_chapter_briefing(chapter_id, llm_fill=True)`** fills
      freeform sections via Driver; decidable sections (mode-block
      status, gate counts) unchanged.
- [ ] **The 13-section template = the cache-stable prefix** (Spec 146);
      per-chapter variables come after the breakpoint.
- [ ] **Briefing checklist (141) re-runs after render.**
- [ ] **Output budget** via Spec 154 if the rendered brief overflows.
- [ ] Test: rendered briefing passes checklist (mocked); cache hits on
      second call.
- [ ] TODO row + drift clean.

## Interconnects

- **LLM-driver chain** (147) · **Output-budget chain** (146/154).
- Spec 237 (scene-brief cache) is the sibling caching pattern.
