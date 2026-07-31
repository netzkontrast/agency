---
spec_id: "237"
slug: scene-brief-cache-discipline
status: draft
state: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "127"
depends_on: ["127", "146", "147", "201"]
vision_goals: [1]
affects:
  - agency/capabilities/prompt/_main.py
  - tests/test_scene_brief_cache.py
---

# Spec 237 — scene-brief cache discipline

## Why

Spec 127 ships `assemble_scene_brief` (7 graph-backed sections, token-
budgeted to 2000). Per the `claude-api` skill, prompt caching works
when the prefix is BYTE-STABLE — but the brief currently orders
sections by graph traversal order, and varies prefix bytes per call
when a section's source data shifts. With Spec 146 prefix discipline
and Spec 201 authoritative token count, the brief gains explicit cache
hygiene: stable sections first, volatile sections after the last
breakpoint, every call counted.

## Done When

- [ ] **`assemble_scene_brief(scene_id) -> SceneBrief`** where
      `SceneBrief = {prefix_bytes: bytes, suffix_bytes: bytes,
      breakpoint_offset: int, prefix_tokens: int, suffix_tokens: int,
      sections: list[Section]}` and `Section = {name, stability:
      Literal["frozen","semi","volatile"], byte_offset, token_count}`.
- [ ] **Section order = stability-descending** — invariant: for any two
      sections `s_i, s_j` with `i < j`, `STABILITY_RANK[s_i.stability]
      >= STABILITY_RANK[s_j.stability]`. Frozen ontology fragments come
      first, semi-stable codex middle, volatile scene-state last.
- [ ] **`cache_control` breakpoint** placed at the last stable section
      (per claude-api skill: max 4 breakpoints, ≥1024-token minimum).
      Invariant: `prefix_tokens >= 1024` (cache eligibility) AND
      `breakpoint_offset == byte_offset of last frozen-or-semi section`.
- [ ] **Prefix byte-stability is RELATIONAL** — invariant: across two
      calls for the same `scene_id` where only volatile sections
      changed, `brief_1.prefix_bytes == brief_2.prefix_bytes` (byte-
      identical, not just hash-equal). Suffix may differ; prefix must
      not. No pinned byte count.
- [ ] **Token counts via Spec 201** when the Driver is the consumer —
      invariant: `prefix_tokens + suffix_tokens == total_tokens`
      reported by `count_tokens`; never a hand-summed estimate.
- [ ] **Verify cache hits** in the test — second call shows
      `cache_read_input_tokens > 0` on a mocked Driver. Invariant:
      `cache_read_input_tokens >= prefix_tokens * 0.9` (allowing for
      tokenizer drift); never a pinned absolute count.
- [ ] **Failure modes** — `scene_id` missing → `Codes.SCENE_NOT_FOUND`;
      prefix below the 1024-token floor → `Codes.CACHE_INELIGIBLE`
      (still returns brief, breakpoint omitted, warning logged so the
      author knows cache is off); Driver rejects breakpoint (model
      doesn't support cache_control) → `Codes.CACHE_UNSUPPORTED`,
      brief returned without breakpoint metadata.
- [ ] Test: prefix bytes stable across 5 calls with identical scene id.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  scene_id S with ontology + codex stable, scene-state edited
        between two assemble calls
When:   brief_1 = assemble_scene_brief(S); edit scene-state;
        brief_2 = assemble_scene_brief(S)
Then:   brief_1.prefix_bytes == brief_2.prefix_bytes AND
        brief_1.suffix_bytes != brief_2.suffix_bytes AND
        both briefs report prefix_tokens >= 1024 AND
        Driver.invoke(brief_2) returns cache_read_input_tokens >=
        brief_2.prefix_tokens * 0.9

Given:  a scene whose ontology+codex sections sum to 800 tokens
When:   assemble_scene_brief(S) runs
Then:   the breakpoint is OMITTED AND Codes.CACHE_INELIGIBLE is logged
        AND the brief is still returned (graceful degrade, never raise)
```

## Interconnects

- **Output-budget chain** (146) anchor consumer.
- Spec 147 + Spec 201 for measured budgets.
- Spec 239 (Dramatica fragments) — fragments are the frozen-section
  source; their byte-stability is this brief's prefix-stability.
- Spec 240 (scene-writer loop) — primary consumer, relies on cache
  hits to keep iterate-to-gate cost bounded.
- Spec 241 (character-knowledge extract) — extract-from-scene shares
  the same prefix budget so cache amortizes across both calls.

## Open questions

1. **Breakpoint count.** One breakpoint or two? **Recommend:** one at
   the frozen/semi boundary; the API allows 4 but the second saves <5%.
2. **Volatile section ordering.** **Recommend:** deterministic
   alphabetical — keeps suffix diffs reviewable.
3. **Cache TTL.** Default 5-min ephemeral or 1-hour? **Recommend:**
   1-hour for scene-writer loop (Spec 240) — the iterate cadence
   exceeds 5 min in real walks.

## Followup — Implementation Status (IMPLEMENTED 2026-07-02, PR #328)

Shipped in `agency/capabilities/prompt/clusters/assembly.py` — TDD, 6 tests
in `tests/test_scene_brief_cache.py`; the Spec-127 acceptance contract
(`tests/acceptance/test_prompt.py`) stays green untouched.

**Done:**
- Stability classes declared per composer INPUT (not per label): frozen =
  storyform; semi = pov_card, voice_constraints; volatile = world_rules
  (it scans the scene cast), scene_cast, continuity, foreshadowing —
  volatile renders alphabetically (Open Q2). Render order IS
  stability-descending; sections_meta ranks asserted non-increasing.
- The brief splits at the frozen/semi ↔ volatile boundary:
  `prompt == prefix + suffix` byte-exact; per-section
  `{name, stability, byte_offset, token_count}` metadata with offsets
  verified against the encoded prompt.
- Prefix byte-stability RELATIONAL: five calls around a cast + body edit
  yield exactly ONE distinct prefix while the suffix moves.
- `cache` block: breakpoint at `len(prefix.encode())` only above the
  floor; `CACHE_MIN_PREFIX_TOKENS = 1024` is a documented tunable with a
  per-call `cache_floor_tokens` override (relation-tested, no fabricated
  1024-token fixture); below-floor → `Codes.CACHE_INELIGIBLE`, driver
  with `supports_cache_control=False` → `Codes.CACHE_UNSUPPORTED` — brief
  returned intact in both.
- Spec 201: a wired `anthropic` driver's `count_tokens` is authoritative
  (`prefix_tokens + suffix_tokens == total_tokens` under the driver
  count); heuristic fallback otherwise.
- Mocked-driver cache-hit proof: the fake only reports
  `cache_read_input_tokens` when the second call's prefix BYTES equal the
  cached ones — `read >= prefix_tokens * 0.9` asserted.
- Robustness fix en route: a Storyform body that JSON-parses to a
  non-dict no longer crashes `_BriefContext.from_scene`.

**Still open (deferred):**
- `Codes.SCENE_NOT_FOUND` typed failure — the Spec-127 acceptance contract
  pins success-with-`error="NOT_FOUND"`; flipping it is a breaking-change
  slice to take together with that suite.
- Second breakpoint (Open Q1) unimplemented — one boundary ships.
- 1-hour TTL (Open Q3) is advisory metadata (`cache.ttl`); enforcement
  lives with the consuming driver (Spec 240 scene-writer loop).
