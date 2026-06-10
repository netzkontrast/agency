---
spec_id: "254"
slug: voice-locked-cache-discipline
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "144"
depends_on: ["144", "237", "146", "147"]
vision_goals: [1, 4]
affects:
  - agency/capabilities/prompt/_main.py
  - tests/test_voice_locked_cache.py
---

# Spec 254 — voice-locked brief: cache discipline

## Why

Spec 144 ships `compose_voice_locked_brief` — Sprach-DNA into a
3000-token brief with non-truncatable §TABOO. The §TABOO + §SYNTAX +
§LEXICON sections are STABLE for an alter; §SCENE BRIEF + §INSTRUCTION
are volatile. The brief is exactly the kind of structured prompt that
benefits from Spec 146/237 cache discipline — alter-stable sections
first with `cache_control`, scene-volatile after the breakpoint.

## Done When

- [ ] **Brief restructured: alter-stable prefix → scene-volatile body** —
      the order Spec 237 codifies; non-truncatable §TABOO stays in the
      prefix.
- [ ] **`cache_control` breakpoint** placed at the last alter-stable
      section.
- [ ] **Per-alter prefix cached across N scenes** — verified in test
      (mocked Driver `cache_read_input_tokens > 0`).
- [ ] **Co-front guard (144) preserved** unchanged.
- [ ] Test: 5 scene briefs for same alter show cache hits 2-5.
- [ ] TODO row + drift clean.

## Interconnects

- **Output-budget chain** (146/237).
- **LLM-driver chain** (147).
