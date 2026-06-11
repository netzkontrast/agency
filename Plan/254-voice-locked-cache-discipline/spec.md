---
spec_id: "254"
slug: voice-locked-cache-discipline
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "144"
depends_on: ["144", "237", "146", "147", "244", "201", "150"]
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
      typed return `VoiceLockedBrief{ prefix: BriefPrefix{taboo_section:
      str, syntax_section: str, lexicon_section: str, alter_id, profile_hash:
      str, prefix_tokens: int}, body: BriefBody{scene_section: str,
      instruction_section: str, scene_id, body_tokens: int}, total_tokens:
      int, cache_breakpoint_offset: int }`. The order Spec 237 codifies;
      non-truncatable §TABOO stays in the prefix.
- [ ] **`cache_control` breakpoint** placed at the last alter-stable
      section — `cache_breakpoint_offset == sum(prefix section
      byte-lengths)`. Test asserts the breakpoint sits AFTER §LEXICON
      and BEFORE §SCENE.
- [ ] **Invariant: per-alter prefix is byte-stable across N scenes** —
      for the same alter + same confirmed VoiceProfile, two calls with
      different scenes produce IDENTICAL `prefix` bytes. Property test
      across 5 scenes: `len(set(call.prefix for call in calls)) == 1`.
- [ ] **Invariant: prefix tokens ≥ cache minimum** —
      `prefix_tokens >= 1024` (Claude API minimum per claude-api skill;
      `>= 4096` for Opus/Haiku 4.5+ parameterized by model). Brief
      assembly pads §LEXICON with the alter's full lexicon corpus
      until threshold met, never trims §TABOO.
- [ ] **Invariant: cache-hit relationship measured, not pinned** — test
      asserts `usage.cache_read_input_tokens > 0` on calls 2..N for
      same alter; AND `usage.cache_creation_input_tokens > 0` on call
      1; AND `cache_read_input_tokens` is approximately equal to
      `prefix_tokens` (within model-dependent tolerance). Spec 201
      provides authoritative counts when `[anthropic]` extra installed.
- [ ] **Invariant: §TABOO is non-truncatable** — even under
      MAX_PREFIX_TOKENS pressure (Spec 146), §TABOO never truncates;
      §LEXICON truncates first. Test asserts a prefix overflow scenario
      produces `Codes.PREFIX_BUDGET_EXCEEDED` rather than silent
      §TABOO trim.
- [ ] **Co-front guard (144) preserved** unchanged — switching alters
      mid-scene rebuilds the brief; the new alter's prefix is cached
      separately (one cache slot per alter).
- [ ] **Failure modes**: profile change between calls (Spec 244 judged
      profile confirmed) → prefix re-hash invalidates cache ONCE,
      then re-stable; Driver `RATE_LIMITED` → retry with same prefix
      (cache still warm); cache TTL expiry (Anthropic ephemeral, ~5
      min) → re-cache transparently, next call after warm-up hits
      again; alter with no drafted scenes → fall back to statistical
      profile (Spec 244 invariant), prefix still byte-stable; profile
      shuffle (key order drift) → sorted-key serialization (Spec 146)
      preserves stability.
- [ ] Test: 5 scene briefs for same alter show cache hits 2-5;
      profile-change call invalidates once then re-stabilizes; mid-
      scene alter switch uses a separate cache slot.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  alter "Mira" with a confirmed VoiceProfile (Spec 244); 5
        scenes drafted requiring voice-locked briefs in sequence
When:   compose_voice_locked_brief(alter="Mira", scene_n) called for
        n in 1..5; AnthropicDriver wraps with cache_control on prefix
Then:   call 1: usage.cache_creation_input_tokens >= 1024;
        calls 2-5: usage.cache_read_input_tokens >= 1024 each;
        brief.prefix bytes identical across calls 1-5;
        brief.body differs each call (scene-specific);
        switching to alter "Alex" on call 6 creates a NEW cache slot
        (call 6 is cache_creation, not cache_read);
        if Mira's voice profile is re-confirmed (244) between calls
        4 and 5, call 5 is cache_creation; call 6 (back to Mira)
        is cache_read against the NEW prefix
```

## Interconnects

- **Output-budget chain** (146/237) — voice-locked brief is the
  canonical case of per-entity cache discipline.
- **LLM-driver chain** (147) — Driver wraps with `cache_control`.
- Spec 244 (voice-profile derive) — confirmed VoiceProfile is the
  alter-stable input; re-derivation invalidates the cache once.
- Spec 201 (TokenCounter API) — authoritative token counts when
  `[anthropic]` extra installed; lint uses local cl100k otherwise.
- **Dogfood-loop chain** (150) — cache-miss patterns (frequent
  prefix invalidation) signal that the profile-derivation cadence
  is too aggressive (Spec 244 recommend re-derive only on demand).

## Open questions

1. **Lexicon padding strategy.** Pad §LEXICON with what content to
   hit the 1024-token threshold? **Recommend**: prefer the alter's
   own drafted-scene lexicon corpus; fall back to canon glossary
   only when alter corpus is short. Never pad with filler — pads
   are signal-bearing.
2. **Multi-alter scene briefs.** When a scene legitimately requires
   2 alters fronting? **Recommend**: concat per-alter prefixes
   sorted by alter_id (stable order) with a single breakpoint at
   the end — one cache slot per "alter-set"; rare enough to accept
   re-cache cost.
3. **Profile-hash granularity.** Hash entire profile, or only
   prefix-affecting fields? **Recommend**: prefix-affecting only
   (taboo, syntax, lexicon) — fields like `emotional_cadence` used
   only in §INSTRUCTION (body) should NOT invalidate the prefix
   when changed.
