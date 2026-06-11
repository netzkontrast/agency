---
spec_id: "256"
slug: anthropic-driver-fallbacks
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "147"
depends_on: ["147", "151", "201", "146", "263", "266"]
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
`BetaFallbackState`) or the server-side `fallbacks` parameter (beta
header `server-side-fallback-2026-06-01`) so a refused request retries
on Opus 4.8 client-side or server-side. Without this, a single safety
classifier hit silently fails every `dogfood.parse_amendment`,
`thinking.*`, and `scene-writer` call running on Fable 5 — the
classifier loop (Spec 150) breaks the moment the model upgrades.

## Done When

- [ ] **`stop_reason: "refusal"` typed handling** — `DriverError.REFUSAL`
      carries `{category, billed_tokens, partial_text}` per claude-api
      skill: pre-output empty (unbilled, `billed_tokens == 0`) vs
      mid-stream partial (`billed_tokens > 0`, `partial_text` preserved
      for the orchestrator). Never crashes; routes through the typed
      Codes envelope (Spec 151).
- [ ] **Server-side `fallbacks` parameter** when on `claude-fable-5`
      using beta header `server-side-fallback-2026-06-01`. Default
      fallback chain: `["claude-opus-4-8", "claude-sonnet-4-7"]`. The
      driver inspects `response.model` to learn which fallback served
      the request and records it as a `DriverEvent("fallback_used",
      requested=..., served=...)`.
- [ ] **Client-side middleware** as Bedrock/Vertex fallback path —
      same observable behaviour (`fallback_used` event, same Codes
      surface), different transport (SDK `BetaRefusalFallbackMiddleware`
      + `BetaFallbackState`).
- [ ] **Token re-baselining via Spec 201** — when the served model
      differs from the requested model, re-count tokens via API count
      and store both as `{requested_model_tokens, served_model_tokens}`
      so the ~30% Fable→Opus delta is observable, not hidden.
- [ ] **Measurable invariants** (not pinned counts):
      - `fallback_chain_length >= 1` whenever `model == "claude-fable-5"`
      - `unbilled_refusal_count / total_refusals` is reported (rate, not
        absolute) — a regression alarm trips when the rate drops below
        the rolling 7-day median by > 20%
      - `served_model in (requested_model, *fallback_chain)` is invariant
        — any other served model is a config bug
- [ ] Test: refused request retries on fallback (mocked); pre-output
      refusal is unbilled (`billed_tokens == 0`); mid-stream refusal
      preserves `partial_text`; `fallback_used` event recorded.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  driver.complete(model="claude-fable-5", messages=[...]) with
        beta server-side-fallback-2026-06-01 enabled, fallbacks=
        ["claude-opus-4-8"]
When:   Fable 5 returns stop_reason: "refusal", category: "cyber"
        BEFORE any output token is emitted (billed_tokens == 0)
Then:   server-side fallback retries on claude-opus-4-8; response.model
        == "claude-opus-4-8"; DriverEvent("fallback_used",
        requested="claude-fable-5", served="claude-opus-4-8") recorded
        AND DriverError.REFUSAL is NOT raised (the fallback succeeded)
        AND the wrapping verb's retry budget is unchanged

Given:  ZDR org with `retention_meets_fable_5 == False` (Spec 170)
When:   any call requests model="claude-fable-5"
Then:   driver returns Result.failure(DriverError.BAD_REQUEST{
        detail:"retention"}) BEFORE the SDK call — never burns a
        request to discover the org constraint

Given:  client-side path (Bedrock), refusal mid-stream after 800 tokens
When:   BetaRefusalFallbackMiddleware re-issues on claude-opus-4-8
Then:   DriverError.REFUSAL is suppressed; the orchestrator receives
        the Opus completion AND a DriverEvent("fallback_used",
        partial_billed_tokens=800) so the cost is observable
```

## Failure modes (Nygard)

| Failure | Driver response |
|---|---|
| `stop_reason: "refusal"` pre-output (unbilled) | Try fallback chain; if exhausted → `DriverError.REFUSAL{billed=0}`; never retry the same model |
| `stop_reason: "refusal"` mid-stream (partial billed) | Preserve `partial_text`; try fallback; record `partial_billed_tokens` in event |
| Beta header rejected by API | Downgrade to client-side middleware; record `DriverEvent("server_fallback_unavailable")` |
| Fallback model also refuses | Walk the rest of `fallbacks=[...]`; if all exhaust → `DriverError.REFUSAL{exhausted: True}` |
| Fable 5 on ZDR org | Pre-flight `BAD_REQUEST{detail:"retention"}` before SDK call (Spec 170 readiness) |
| Fallback chain misconfigured (cycle / missing model) | Fail fast at driver init with `DriverError.AUTH_FAILED{detail:"fallback_config"}` |
| Token-count mismatch between requested + served model | Both counts stored; the ~30% delta is observable, not silently swallowed |

## Interconnects

- Spec 147 (parent driver) — extends `DriverError` enum with the
  refusal sub-states and adds `fallbacks` to the `complete` surface.
- Spec 151 (typed Codes) — `REFUSAL`, `REFUSAL_EXHAUSTED`,
  `FALLBACK_CONFIG_INVALID` land here.
- Spec 201 (TokenCounter API) — re-baselines when served model differs.
- Spec 146 (output-prefix) — fallback path MUST preserve prefix-stable
  envelope so caching survives the model swap (the prefix is model-agnostic).
- Spec 263 (Fable 5 extras) — defines the request-shape constraints
  (no `temperature`, omit `thinking`) that the fallback chain inherits.
- Spec 170 (doctor) — `retention_meets_fable_5` gates Fable 5 dispatch.
- Spec 266 (code-mode error boundary) — refusal mid-chain capture-recall
  works because this spec keeps the partial billable text observable.
- Spec 258 (dogfood quality loop) — depends on refusal NOT crashing
  the classifier; the rubric-eval cycle relies on this fallback.
- **LLM-driver chain** completion.

## Open questions

1. **Default fallback chain order.** Fable 5 → Opus 4.8 → Sonnet 4.7,
   or Fable 5 → Opus 4.8 only? **Recommend**: two-step (Fable 5 →
   Opus 4.8) by default; the third hop costs latency without
   meaningfully changing refusal probability (Opus 4.8 and Sonnet 4.7
   share the safety classifier family). Operators override via config.
2. **Should mid-stream refusal billed tokens count against intent
   budget?** **Recommend**: yes — they were emitted by the model and
   the wrapping verb saw them. Hiding them creates a leak.
3. **Server-side vs client-side preference when both available?**
   **Recommend**: server-side first (single round-trip, no extra
   client logic); client-side only when the beta header is rejected
   or when the transport is Bedrock/Vertex which do not yet support
   the server-side beta.
