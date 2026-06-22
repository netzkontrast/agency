---
spec_id: "257"
slug: output-prefix-managed-cache
status: draft
state: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "146"
depends_on: ["146", "237", "254", "201", "147", "262"]
vision_goals: [1]
affects:
  - agency/_envelope.py
  - tests/test_managed_cache_proof.py
---

# Spec 257 — output-prefix: Managed-Agents cache proof

## Why

Spec 146 anchors the output-budget chain — every substrate-tool
response carries a frozen `prefix` + per-call `body` so the Claude
API's prefix-match prompt cache rewards the wrapper. The Managed-Agents
surface (claude-api skill `shared/managed-agents-core.md`) layers its
OWN built-in prompt caching + context compaction on top: when the
engine is wrapped inside a Managed-Agent session, the prefix has to
survive both caches AND survive compaction without being dropped from
`response.content`. Today that compose is unverified; without proof,
the engine's prefix-stability invariant lapses silently the moment
agency is dispatched into a Managed-Agent harness (Goal 8, the
harness-in-harness recursion).

## Done When

- [ ] **Cross-session prefix-stability test** — engine response
      `envelope.prefix` is byte-identical across two Managed-Agent
      sessions sharing a single persisted Agent (Spec 137 Lock
      `agent_id`). Both sessions report
      `usage.cache_read_input_tokens > 0` on the second call.
- [ ] **Compaction-block preservation** — when the Managed-Agent
      session triggers context compaction, the substrate-tool
      `envelope.prefix` MUST appear unchanged in `response.content`
      after compaction (verified by comparing pre/post-compaction
      message blocks). The `response.content` discipline (claude-api
      skill) is the canonical preservation mechanism.
- [ ] **Documented compose pattern** in `docs/architecture/envelope.md`
      showing the recommended `cache_control` placement when wrapping
      agency in a Managed-Agents harness (one breakpoint on the
      Agent system prompt, one on the engine prefix).
- [ ] **Measurable invariants** (computed, not pinned):
      - `prefix_bytes_pre_compaction == prefix_bytes_post_compaction`
        whenever capability set is unchanged
      - `cache_read_input_tokens > 0` on second call within a session
        AND across sessions sharing the same Agent
      - `compaction_drop_count == 0` for substrate-tool blocks — they
        are always preserved
- [ ] Test: prefix bytes stable across mocked Managed-Agents sessions;
      compaction preserves the substrate-tool envelope; cache-read
      tokens exceed zero on second call.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  agency engine wrapped in a Managed-Agent session sharing
        persisted Agent A (Spec 137); session 1 just completed; session 2
        starts against the same A with the same capability set
When:   session 2 calls agency_welcome() for the first time
Then:   envelope.prefix bytes are byte-identical to session 1's
        AND response.usage.cache_read_input_tokens > 0
        AND the Managed-Agent's outer cache ALSO reports a hit on the
        Agent system prompt

Given:  session 2 mid-way; context window approaches limit;
        Managed-Agent triggers compaction
When:   compaction completes and the next substrate tool returns
Then:   the substrate-tool envelope.prefix bytes are unchanged from
        pre-compaction; the prefix block was preserved verbatim in
        response.content (not summarized away)
```

## Failure modes (Nygard)

| Failure | Engine response |
|---|---|
| Managed-Agent compaction drops the substrate-tool block | Emit `Codes.PREFIX_DROPPED_BY_COMPACTION`; the compose-pattern doc warns operators to whitelist substrate blocks |
| Outer cache (Agent prompt) invalidated mid-session | Engine prefix cache continues working independently; observability records `outer_cache_miss + inner_cache_hit` |
| Agent ID mismatch across sessions | Pre-flight `Codes.AGENT_ID_MISMATCH`; never silently splits the cache namespace |
| Beta header `extended-cache-ttl-2025-04-11` unavailable | Engine falls back to ephemeral cache; the test asserts the chosen tier, not a fixed TTL |

## Interconnects

- Spec 146 (parent) — extends the prefix discipline across the
  Managed-Agent boundary.
- Spec 237 (dynamic-prompt slice-2 cache) — sibling cache discipline
  for prompt-side prefixes; this spec proves substrate-side composes
  with it.
- Spec 254 (voice-locked cache discipline) — sibling for creative
  cluster; shares the cache-stability invariant.
- Spec 201 (TokenCounter API backend) — authoritative cache token
  counts come from API count, not local cl100k.
- Spec 147 (AnthropicDriver) — the Driver places `cache_control` on
  both the outer Agent prompt and the inner substrate prefix.
- Spec 262 (managed-agents onboarding cap) — the most common path
  that lands agency inside a Managed-Agent session; this spec
  certifies the cache survives that path.
- **Output-budget chain** completion across the MA bridge.

## Open questions

1. **Cache TTL on the substrate prefix when nested.** Inherit the
   Managed-Agent's TTL, or override? **Recommend**: inherit — the
   outer harness owns the lifecycle; overriding fragments the cache.
2. **Should compaction preserve `body` too, or only `prefix`?**
   **Recommend**: only `prefix` — `body` is per-call ephemeral by
   construction; preserving it across compaction would defeat the
   point of compaction.
3. **How is the cache compose verified in CI without a live API
   key?** **Recommend**: mocked SDK with a recorded usage envelope
   (the `claude-api` skill ships fixture shapes); live verification
   gated on `live_anthropic` pytest mark (same gate as Spec 147).
