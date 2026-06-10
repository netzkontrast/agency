---
spec_id: "256"
slug: anthropic-driver-fallbacks
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "147"
depends_on: ["147", "151", "201", "146"]
vision_goals: [3]
affects:
  - agency/_drivers/_anthropic.py
  - tests/test_anthropic_driver_fallbacks.py
---

# Spec 256 — AnthropicDriver: refusal fallback + Fable 5

## Why

Spec 147 anchors the LLM-driver chain. Per `claude-api` skill, Claude
Fable 5 changes the request surface (always-on protected thinking, no
`temperature`/`top_p`/`top_k`, new tokenizer ~30% more tokens, possible
`stop_reason: "refusal"` on safety classifiers). Production drivers
need the SDK fallback middleware (`BetaRefusalFallbackMiddleware` +
`BetaFallbackState`) or the server-side `fallbacks` parameter so a
refused request retries on Opus 4.8 client-side or server-side.

## Done When

- [ ] **`stop_reason: "refusal"` handled** — pre-output empty (unbilled)
      vs mid-stream partial; never crashes; tagged failure result
      (Spec 151 Codes).
- [ ] **Server-side `fallbacks` parameter** when on `claude-fable-5`
      (Claude API, beta `server-side-fallback-2026-06-01`); pin
      `claude-opus-4-8` as the fallback by default.
- [ ] **Client-side middleware** as a Bedrock/Vertex fallback path —
      same behaviour, different transport.
- [ ] **Token re-baselining** via Spec 201 when on Fable 5 (~30% delta).
- [ ] Test: refused request retries on fallback (mocked); pre-output
      refusal is unbilled.
- [ ] TODO row + drift clean.

## Interconnects

- Spec 147 (parent driver); Spec 151 (typed Codes); Spec 201 (API count).
- **LLM-driver chain** completion.
