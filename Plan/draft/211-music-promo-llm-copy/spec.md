---
spec_id: "211"
slug: music-promo-llm-copy
status: draft
state: draft
last_updated: 2026-06-11
owner: "@agency"
enhances: "098"
depends_on: ["098", "147", "119", "150", "146", "206", "216"]
vision_goals: [4, 1]
affects:
  - agency/capabilities/music/_main.py
  - agency/capabilities/music/clusters/promo.py
  - tests/test_music_promo_llm.py
---

# Spec 211 — music promo LLM copy generation

## Why

Spec 098 (music-promo) ships 8 verbs for platform-specific promo +
`promo_review` (which Spec 119 extended with name-exposure scanning).
Like lyrics (Spec 208), the actual COPY is written in chat. The agency
port should make `write_promo(platform)` a verb: the Spec 147 Driver
drafts platform-tuned copy from the album themes + track concepts, and
the shipped `promo_review` + name-exposure gates (Spec 119) validate it.

## Done When

- [ ] **`write_promo(album_id, platform, max_iterations=2)`** drives the
      Spec 147 Driver with album themes + the platform template; output
      runs through the shipped `promo_review` + name-exposure gate
      (Spec 119). Typed return: `PromoResult = {album_id, platform,
      copy_md: str, char_count: int, iterations: int,
      review_verdict: GateVerdict, name_exposure_verdict: GateVerdict,
      driver_usage: TokenUsage, reflection_id: NodeId}`.
- [ ] **Name-exposure (Spec 119) blocks** a generated post that leaks a
      blocklisted name — the gate is non-negotiable; failure short-
      circuits return BEFORE the promo lands in `content_root`.
- [ ] **Generation honors the output budget** (Spec 146); the
      album-theme + platform-template prefix is cache-stable across all
      platforms for the same album.
- [ ] **Drafts record Reflections** (Spec 150) — every iteration carries
      the platform + iteration number in scope so the dogfood loop can
      learn per-platform tone drift.
- [ ] **Degrades** to the template scaffold without `[anthropic]`.
- [ ] **Test**: generated copy passes review; a name leak blocks
      (mocked Driver); the same album yields cache-hit on the second
      platform's prompt.
- [ ] **TODO row + drift clean.**

## Measurable invariants (relationships, not pinned counts)

- **Per-platform character budget** — `char_count <=
  PLATFORM_LIMIT[platform]` for every successful return (derived from
  platform metadata, not pinned per-platform here); failure surfaces as
  `Codes.PROMO_OVER_BUDGET`.
- **Hard-gate non-skip** — for every returned `PromoResult` with status
  `passed`, BOTH `review_verdict.passed and name_exposure_verdict.passed`;
  no soft-skip path.
- **Cross-platform prefix stability** — `write_promo(album, "X")` and
  `write_promo(album, "instagram")` share an identical system-prompt
  prefix up to the platform-template boundary (Spec 146 cache).
- **Iteration provenance** — `iterations` matches the number of
  Reflections scoped to `(album_id, platform)` for this call.

## Worked example (Given/When/Then)

```text
Given:  album_id with themes "loss, late-night drive"; platform="X";
        AnthropicDriver mocked to return a 240-char draft that mentions
        a blocklisted name on iteration 1, then a clean draft on iter 2
When:   write_promo(album_id, "X", max_iterations=2)
Then:   returns PromoResult{iterations=2, copy_md=clean,
        char_count<=280, review_verdict.passed=True,
        name_exposure_verdict.passed=True}
        AND 2 Reflections SERVE the album_id with platform="X" in scope
        AND a follow-up write_promo(album_id, "instagram") sees
        usage.cache_read_input_tokens > 0 on the shared theme prefix
```

## Failure modes (Nygard)

| Failure | Verb response |
|---|---|
| Driver `REFUSAL` | typed failure; Reflection emitted; never silent retry |
| Driver `RATE_LIMITED` | driver-owned backoff; iteration counter preserved |
| Name-exposure leak on EVERY iteration | return `PromoResult` with `name_exposure_verdict.passed=False`; copy NOT written to `content_root`; caller decides |
| Platform character budget exceeded | typed failure; never silently truncate (truncation drops the CTA, which is the post) |
| `[anthropic]` extra missing | typed degraded result — scaffold returned with `driver_usage=zero()` |
| `content_root` missing for the album | typed failure BEFORE driver call (zero spend); Spec 215 doctor hint |
| Generated copy lands a banned hashtag (future Spec 119 extension) | extension hook returns `BLOCKED`; same hard-gate behaviour |

## Interconnects

- **LLM-driver chain** (147) · **dogfood** (150) · **output-budget** (146).
- Spec 119 (name-exposure) is the hard gate on generated copy.
- Spec 216 (shared name-exposure check) is the substrate this calls;
  music + novel share one implementation.
- Spec 206 (produce-album walk) drives this as the promo phase, one
  per platform.
- Spec 208 (lyrics LLM) — sibling LLM-generation verb sharing the
  iterate-to-gate pattern.

## Open questions

1. Per-platform or one draft adapted? **Recommend**: per-platform (the
   templates differ); shared theme prefix is cache-stable (Spec 146).
2. Bounded retry budget per album release? **Recommend**: yes — sum of
   `iterations` across all platforms for one album ≤ a config cap (e.g.
   20) so a misbehaving Driver can't drain a billing budget.
3. Where do platform character limits live? **Recommend**: derived from
   the platform metadata graph nodes (rule 8); never hardcoded per-
   platform in this verb.
