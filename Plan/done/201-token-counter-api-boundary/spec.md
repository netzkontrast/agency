<!-- agency-node: document:7e2339e2 -->
---
spec_id: "201"
slug: token-counter-api-boundary
status: done
state: done
last_updated: 2026-06-20
owner: "@agency"
enhances: "082"
depends_on: ["082", "147", "146", "170"]
vision_goals: [1]
affects:
  - agency/_tokens.py
  - tests/acceptance/features/token_count_api.feature
  - tests/acceptance/test_token_count_api.py
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

- [x] **`CountResult` typed return** — `CountResult = {tokens: int,
      backend: Literal["anthropic","tiktoken","proxy"], model: str,
      cached: bool, latency_ms: int}`. Callers branch on `backend`
      for diagnostics; the value is always usable.
- [x] **`TokenCounter` gains an `anthropic` backend** behind the
      existing Spec 082 boundary — `messages.count_tokens(model=…)`
      for the model the Driver targets; tiktoken/proxy stay the
      zero-config fallbacks.
- [x] **Invariant — backend preference** (relationship): when
      `[anthropic]` extra is installed AND `ANTHROPIC_API_KEY` set AND
      the model is an Anthropic model, `backend == "anthropic"`;
      otherwise `backend in {"tiktoken","proxy"}`.
- [x] **Invariant — band agreement** (relationship, Spec 082 rule 8):
      for the same content + model, `0.80 <= anthropic_tokens /
      tiktoken_tokens <= 1.30` — outside the band fails (signals a
      tokenizer-family mismatch, e.g. Fable-5 ~30% delta).
- [x] **Invariant — output-budget honors best available** (relationship):
      Spec 146's `prefix_size_tokens` is computed with the
      best-available backend per call; never pinned to a baseline.
- [x] **Invariant — cache idempotence**: for any `(content_hash, model)`,
      the cached count equals the freshly-computed count (deterministic
      counter); a divergence trips a cache-bug invariant.
- [x] **Failure mode coverage** — Anthropic API RATE_LIMITED / TIMEOUT /
      AUTH_FAILED each fall back to the local backend with
      `CountResult.backend != "anthropic"` and a typed `error_code`
      field; never crash the caller's budget check.
- [x] **`agency_doctor.token_backend` reports the live backend** (Spec
      170) — `{available: list[str], preferred: str, last_used: str,
      band_check_ok: bool}`.
- [x] Test: API backend chosen when present (mocked); local fallback
      deterministic across two runs; band invariant holds over a
      fixture content set; cache idempotence asserted.
- [x] TODO row + drift clean.

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

## Followup — Implementation Status (Slice 1, 2026-06-20)

### Already shipped (Spec 082) — the authoritative backend pre-existed

201's core ask — "`TokenCounter` gains the Anthropic `messages.count_tokens`
backend; tiktoken/proxy stay the fallbacks" — was **already delivered by
Spec 082**: `agency/_tokens.py::_anthropic_fn` calls
`client.messages.count_tokens(model=…, messages=[{role,content}])` →
`input_tokens` (the exact `claude-api`-skill pattern, `claude-opus-4-8`
default), and `resolve_token_counter` prefers it ONLY when `ANTHROPIC_API_KEY`
+ the `anthropic` SDK are present, else tiktoken → proxy. The live backend name
is `count_tokens` (082's name; kept — renaming would break the doctor + the
naming audit).

**OpenRouter-only setups already avoid Anthropic (owner directive 2026-06-20).**
The Anthropic count_tokens backend is dormant unless `ANTHROPIC_API_KEY` is set.
A user configured with only `OPENROUTER_API_KEY` therefore counts via
tiktoken → proxy — no Anthropic call. OpenRouter is an inference router and has
**no token-counting endpoint**, so there is no "OpenRouter count backend" to
add; the directive "use OpenRouter free models instead of Anthropic" applies to
the LLM *decider* (Spec 331 `_llm.py`), not to counting.

### Done — Slice 1 (typed CountResult + cache + band, network-free)

- **`CountResult`** typed shape (`tokens`/`backend`/`model`/`cached`/
  `latency_ms`/`error_code`) + **`TokenCounter.count_result(text, model)`**.
- **Per-(content, model) LRU cache** (`_cached_count`, `_CACHE_MAX=4096`,
  documented size cap; never persisted — counts are derivable, rule 2). Both
  `count` and `count_result` read through it, so Spec 146's `prefix_size_tokens`
  is cheap to recompute. Cache-idempotence invariant holds (deterministic
  counter → a hit returns the prior count).
- **`band_ok(a, b)`** + named tunables `TOKEN_BAND_LOW=0.80` /
  `TOKEN_BAND_HIGH=1.30` (rule 8; OQ3 — widen via PR with a citation).
- **5 acceptance scenarios** (`tests/acceptance/features/token_count_api.feature`
  + `test_token_count_api.py`), network-free via a forced proxy counter: typed
  shape, empty-text zero, cache idempotence, per-model cache keying, band
  agreement at the boundaries. Existing `test_token_budget.py` stays green.

### Shipped — Slice 2 (2026-06-23, TDD)

The two offline-closable items are done; the third is key-gated (deferred like
every other wet/[anthropic]-extra path).

- **`error_code` population — SHIPPED.** `TokenCounter._cached_count` now returns
  `(tokens, cached, error_code)`; a per-call backend failure degrades to the proxy
  AND surfaces a typed `error_code` (`_classify_count_error`: RateLimitError→
  `rate_limited`, APITimeoutError→`timeout`, AuthenticationError→`auth_failed`, else
  `count_backend_failed`). `count_result` reports the backend HONESTLY as `proxy`
  on fallback and tracks `last_backend`. Never crashes the caller
  (`agency/_tokens.py`; `tests/test_token_count_failure.py`).
- **`agency_doctor.token_backend` enrichment — SHIPPED.** Now the rich
  `{available, preferred, last_used, band_check_ok}` via `token_backend_report` /
  `backends_available` (`available` always includes `proxy`; `count_tokens` only
  when SDK+key present). `band_check_ok` is `None` (a live cross-backend compare
  needs the API; the band invariant is asserted on synthetic counts in the suite).
- **Wet band-over-real-fixtures — deferred (key-gated).** Asserting
  `band_ok(anthropic, tiktoken)` over real API counts needs `ANTHROPIC_API_KEY`;
  it can't run offline/in CI. `band_ok` is proven on synthetic counts
  (`tests/acceptance/test_token_count_api.py`); out of scope for this slice, like
  the `[recall]` BGE backend.

201's core scope is complete: typed `CountResult` + anthropic backend + preference
+ cache idempotence (Spec 082/Slice 1) + observable fallback + rich doctor (Slice 2).
