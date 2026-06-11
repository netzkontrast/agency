---
spec_id: "201"
slug: token-counter-api-boundary
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "082"
depends_on: ["082", "147", "146", "170"]
vision_goals: [1]
affects:
  - agency/_token_counter.py
  - tests/test_token_counter_api.py
---

# Spec 201 — TokenCounter Anthropic-API backend

## Why

Spec 082 ships one `TokenCounter` boundary (count_tokens → tiktoken →
proxy). The local backends approximate; the AUTHORITATIVE count for a
Claude model is `messages.count_tokens` (`claude-api` skill,
`shared/token-counting.md` — "do not use tiktoken; it undercounts
Claude tokens by ~15-20%"). The output-budget discipline (Spec 146)
budgets against a count that's wrong by up to 20%. When the Spec 147
Driver is present, the boundary should prefer the API count for the
model in use.

## Done When

- [ ] **`CountResult` typed return** — `CountResult = {tokens: int,
      backend: Literal["anthropic","tiktoken","proxy"], model: str,
      cached: bool, latency_ms: int}`. Callers branch on `backend`
      for diagnostics; the value is always usable.
- [ ] **`TokenCounter` gains an `anthropic` backend** behind the
      existing Spec 082 boundary — `messages.count_tokens(model=…)`
      for the model the Driver targets; tiktoken/proxy stay the
      zero-config fallbacks.
- [ ] **Invariant — backend preference** (relationship): when
      `[anthropic]` extra is installed AND `ANTHROPIC_API_KEY` set AND
      the model is an Anthropic model, `backend == "anthropic"`;
      otherwise `backend in {"tiktoken","proxy"}`.
- [ ] **Invariant — band agreement** (relationship, Spec 082 rule 8):
      for the same content + model, `0.80 <= anthropic_tokens /
      tiktoken_tokens <= 1.30` — outside the band fails (signals a
      tokenizer-family mismatch, e.g. Fable-5 ~30% delta).
- [ ] **Invariant — output-budget honors best available** (relationship):
      Spec 146's `prefix_size_tokens` is computed with the
      best-available backend per call; never pinned to a baseline.
- [ ] **Invariant — cache idempotence**: for any `(content_hash, model)`,
      the cached count equals the freshly-computed count (deterministic
      counter); a divergence trips a cache-bug invariant.
- [ ] **Failure mode coverage** — Anthropic API RATE_LIMITED / TIMEOUT /
      AUTH_FAILED each fall back to the local backend with
      `CountResult.backend != "anthropic"` and a typed `error_code`
      field; never crash the caller's budget check.
- [ ] **`agency_doctor.token_backend` reports the live backend** (Spec
      170) — `{available: list[str], preferred: str, last_used: str,
      band_check_ok: bool}`.
- [ ] Test: API backend chosen when present (mocked); local fallback
      deterministic across two runs; band invariant holds over a
      fixture content set; cache idempotence asserted.
- [ ] TODO row + drift clean.

## Worked example (Given/When/Then)

```text
Given:  ANTHROPIC_API_KEY set, [anthropic] installed, model =
        "claude-opus-4-8", content = "Summarize chapter 1"
When:   TokenCounter.count(content, model) runs (cache cold)
Then:   CountResult{tokens: 6, backend:"anthropic", cached: false,
        latency_ms <= 500}
        AND second call with same (content, model) returns cached: true
        with latency_ms <= 5

Given:  [anthropic] not installed
When:   TokenCounter.count(content, "claude-opus-4-8") runs
Then:   CountResult{backend:"tiktoken", cached: false}
        AND the value is within the band of the API count when
        compared against a fixture-recorded API count

Given:  Anthropic API returns RATE_LIMITED
When:   TokenCounter.count runs
Then:   falls back to tiktoken; CountResult.backend == "tiktoken"
        AND agency_doctor.token_backend.last_used reflects the
        fallback — never crashes the caller's budget check
```

## Failure modes (Nygard)

| Failure | Counter response |
|---|---|
| Anthropic API `RATE_LIMITED` | retry once with backoff; on second fail, local fallback |
| Anthropic API `TIMEOUT` | local fallback; `error_code:"timeout"` in CountResult |
| Anthropic API `AUTH_FAILED` | local fallback; doctor surfaces hint |
| Unknown model id | typed `BAD_REQUEST{detail:"model"}` — never silently default |
| Band-check fail (anthropic vs tiktoken delta > 30%) | log + accept; signals Fable-style tokenizer divergence; doctor flags |
| Cache divergence (same input, different count) | hard invariant fail — counter bug, not a transient |
| Network outage | local fallback; doctor's `available` list updates |

## Interconnects

- **LLM-driver chain** (147) · **output-budget chain** (146).
- Spec 170 (doctor) reports the backend + band-check status.
- Spec 200 (adaptive walk) — per-phase budgets consume the best-available
  count; backend choice surfaced for debugging.
- Spec 198 (CLI parity) — bash-only Jules consumes the local backend;
  parity gate tolerates the band but asserts shape equality.
- Spec 146 (output-prefix) — `prefix_size_tokens` reads through this
  counter; cache idempotence keeps the prefix invariant computable
  cheaply.
- Spec 263 (Fable-5 extras) — Fable model ids route to the Anthropic
  backend with the ~30% tokenizer delta accepted in the band.

## Open questions

1. Cache API counts (they cost a round trip)? **Recommend**: yes,
   per `(content_hash, model)` — counting is deterministic for a given
   model; LRU bound with documented size cap (not a frozen entry count).
2. Where does the cache live? **Recommend**: in-process LRU for
   per-session speed; never persisted to the graph (counts are derivable,
   not provenance — CLAUDE.md rule 2).
3. How does the band threshold evolve as Anthropic ships new tokenizers?
   **Recommend**: the band is a named config constant
   (`TOKEN_BAND_LOW=0.80`, `TOKEN_BAND_HIGH=1.30`); widen via PR with a
   `claude-api` skill citation — never silently relaxed.
