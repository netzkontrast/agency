---
spec_id: "251"
slug: chapter-briefing-llm-render
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "141"
depends_on: ["141", "147", "237", "146", "154", "243", "248", "150"]
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

- [ ] **`render_chapter_briefing(chapter_id, llm_fill=True) ->
      ChapterBriefing`** — typed return `ChapterBriefing{ chapter_id,
      sections: dict[SectionId, SectionContent], decidable_sections:
      list[SectionId], judged_sections: list[SectionId], checklist:
      ChecklistResult, prefix_tokens: int, body_tokens: int, status:
      Literal["proposal","approved"] }`. Decidable sections fill
      first, deterministically; Driver fills freeform sections
      (rationale, open-questions, callbacks); the union obeys the
      141 13-section template.
- [ ] **Invariant: template prefix is byte-stable across renders** —
      the 13-section template skeleton + project-level constants
      hash-stable; Spec 146 `prefix_stability.drift_bytes == 0`
      between two renders of distinct chapters in the same project.
- [ ] **Invariant: decidable sections never delegate to Driver** —
      mode-block status, gate counts, beat-anchor list (Spec 243),
      plural-character roster (Spec 248) are GRAPH READS, not Driver
      output. Property test asserts these sections produce identical
      bytes regardless of `llm_fill` flag value.
- [ ] **Invariant: judged sections always carry rationale** — every
      Driver-filled section ships with a `provenance: {driver_model,
      source_node_ids: list[NodeId], rationale: str}` block; no
      orphan prose. Relationship: `count(judged_sections) ==
      count(provenance blocks)`.
- [ ] **Briefing checklist (141) re-runs after render** — and the
      result is part of the typed return; a checklist FAIL surfaces
      as `status="proposal_incomplete"`, never silently ships.
- [ ] **Output budget** — `body_tokens <= MAX_BRIEF_BODY_TOKENS`
      (Spec 154 default 4000); overflow truncates the freeform
      callbacks section (lowest priority), NEVER the decidable
      ones — and emits `Codes.BRIEF_BODY_TRUNCATED` (Spec 151).
- [ ] **Failure modes**: Driver `REFUSAL` on edgy chapter → fall back
      to decidable-only render with `judged_sections=[]` + log Spec
      150; `RATE_LIMITED` → retry per Spec 147; cache invalidation
      from template-prefix edit (project rename) → re-warm on next
      render, second call hits cache; chapter with no graph context
      (orphan) → render fails closed with `Codes.CHAPTER_ORPHAN`.
- [ ] Test: rendered briefing passes checklist (mocked); cache hits
      on second call across chapters of same project; decidable
      sections byte-identical with and without `llm_fill`.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  a 40-chapter novel; chapter 17 with 3 anchored beats (Spec
        243), 2 active mode-blocks, 4 plural-character co-fronts
        (Spec 248); the 13-section template lives in the cache-
        stable prefix
When:   render_chapter_briefing(chapter_17_id, llm_fill=True) runs;
        the AnthropicDriver fills sections 8 (rationale), 11 (open-
        questions), 13 (callbacks) via output_config.format; then
        render_chapter_briefing(chapter_18_id, llm_fill=True)
Then:   call 1: prefix_tokens >= 1024 (cache minimum);
        decidable_sections contains beat-anchors + mode-blocks
        verbatim from graph; judged_sections each carry provenance;
        checklist passes; status="proposal".
        call 2: cache_read_input_tokens > 0 (prefix hit); body
        re-fills for chapter 18; decidable sections recomputed from
        graph, not LLM
```

## Interconnects

- **LLM-driver chain** (147) — Driver fills the freeform sections.
- **Output-budget chain** (146/154) — template = prefix; per-chapter
  data = body; freeform overflow truncates from lowest priority.
- Spec 237 (scene-brief cache) — sibling caching pattern; both
  share the prefix discipline.
- Spec 243 (structure anchors) — anchored beats are a decidable
  section input.
- Spec 248 (plural-character query) — character roster comes from
  the graph-query substrate, NOT the Driver.
- **Dogfood-loop chain** (150) — repeated checklist failures on the
  same section signal template gaps.

## Open questions

1. **Section priority on overflow.** Which sections truncate first?
   **Recommend**: lowest priority = callbacks → open-questions →
   rationale; NEVER decidable sections or §TABOO-equivalent
   (mode-block status).
2. **Per-section Driver call vs. one call.** Single call fills all
   judged sections, or one call per section? **Recommend**: single
   call with `output_config.format` returning the section dict —
   one API hop, one cache prefix, lower latency.
3. **Re-render cadence.** Auto re-render on graph mutation?
   **Recommend**: no — re-render is on-demand only; auto re-render
   burns cache invalidations. Surface a "stale: bool" flag from
   change-tracking.
