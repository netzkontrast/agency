---
spec_id: "146"
slug: engine-output-prefix-discipline
status: draft
last_updated: 2026-06-10
owner: "@agency"
enhances: "023"
depends_on: ["023", "067", "082", "147", "149"]
vision_goals: [1, 6]
affects:
  - agency/_envelope.py
  - agency/_lints/_response_prefix.py
  - tests/test_response_prefix_discipline.py
---

# Spec 146 — Engine output-prefix discipline (cache-friendly substrate)

## Why

Spec 023 ships token-budget slicing; Spec 067 ships *name* token-budget
lint. Neither budgets the BYTES returned by `mcp__agency__{search,
get_schema, execute}` to the LLM driver that wraps the engine. The
Claude API's prompt-caching is a **prefix match** — any byte change
anywhere in the prefix invalidates everything after it (`claude-api`
skill, `shared/prompt-caching.md`). Today substrate-tool responses
interpolate `datetime.now()` ISO timestamps + intent-id UUIDs into the
HEAD of every response — silently invalidating every wrapper's cache.

## Done When

- [ ] **`agency/_envelope.py` defines `ResponseEnvelope{prefix, body}`** —
      `prefix` = `{schema_version, capability_set_hash, ontology_hash}`
      (frozen per build); `body` = `{intent_id, timestamps, payload,
      next_cursor}` (per-call). Serializer renders `prefix` then `body`
      in deterministic key order (sorted JSON). The Claude API caller
      places `cache_control: {type: "ephemeral"}` on the prefix.
- [ ] **`_check_response_prefix` lint rule** (Spec 067 family, AST):
      flags `datetime.now()`/`time.time()`/`uuid4()`/unsorted-dict and
      any read of `os.environ` resolving at request-time inside any
      function reachable from a substrate-tool's prefix builder. WARN
      one cycle (Spec 056/058 pattern), then promote to **error** once
      the live registry reports zero violations.
- [ ] **`agency_doctor` reports `prefix_stability`** = `{stable: bool,
      drift_bytes: int, drift_tokens: int, prefix_size_tokens: int}` —
      drift is the byte-delta of `prefix` across two `agency_welcome`
      calls separated by 60s. Invariant: `drift_bytes == 0` whenever the
      capability set has not changed. Token count via Spec 082 locally,
      Spec 201 API count when `[anthropic]` extra installed.
- [ ] **Cache-hit invariant test** — beyond byte-stability, exercise the
      Claude API path with a mocked client: assert
      `usage.cache_read_input_tokens > 0` on the second call against the
      live `agency_welcome` prefix (≥ 1024 tokens — claude-api skill
      minimum). On Opus 4.6/4.8 and Haiku 4.5 the minimum is 4096; the
      test parameterizes by model.
- [ ] **Failure mode: prefix overflow** — when capability set grows
      such that the prefix exceeds `MAX_PREFIX_TOKENS` (a configured
      budget, default 8000 tokens), the envelope must REJECT the
      response with `Codes.PREFIX_BUDGET_EXCEEDED` (Spec 151) — never
      silently truncate the prefix, which would partial-cache.
- [ ] **TODO row + drift clean.**

## Worked example (Given/When/Then)

```text
Given:  capability set unchanged between calls
When:   call agency_welcome() twice 60s apart with an LLM driver wrapping
        the engine, cache_control on prefix
Then:   response 2's usage.cache_read_input_tokens > 0 AND
        envelope.prefix bytes are byte-identical to response 1's

Given:  a verb's prefix-builder calls datetime.now()
When:   _check_response_prefix lint runs (post-WARN cycle)
Then:   lint fails with PREFIX_NONDETERMINISTIC pointing at the call site

Given:  capability count grows past MAX_PREFIX_TOKENS
When:   any substrate tool returns
Then:   response carries Codes.PREFIX_BUDGET_EXCEEDED — never silent
        truncation that would partial-cache
```

## Interconnects

- Drives the **output-budget chain** the charter declares.
- Spec 147 (AnthropicDriver) honors the prefix split: every wrapped
  call ships `cache_control: {type:"ephemeral"}` on the prefix.
- Spec 149 (derived docs) consumes `prefix_stability` as a derived
  field; treats `drift_bytes > 0 without capability-set change` as a
  drift bug.
- Spec 154 (output-overflow) caps body, never prefix.
- Spec 201 (TokenCounter API backend) provides authoritative counts
  when the `[anthropic]` extra is installed.
- Spec 257 (managed-agents cache proof) re-verifies prefix-stability
  across Managed-Agents session boundaries.
- Spec 151 (Codes coverage) supplies `PREFIX_BUDGET_EXCEEDED` +
  `PREFIX_NONDETERMINISTIC`.

## Open questions

1. **Token count source.** Use `messages.count_tokens(model=...)` for
   measured budgets, or stick to local cl100k via Spec 082?
   **Recommend**: both — local for lint speed (sub-ms), API call when
   `[anthropic]` extra installed and verifying `prefix_stability`
   (per `claude-api` skill: "do not use tiktoken; it undercounts
   Claude tokens by ~15–20%").
2. **MAX_PREFIX_TOKENS default.** Hard-cap or soft-warn? **Recommend**:
   soft-warn at 6000, hard-fail at 8000 — leaves headroom above the
   tiered-discovery payload (Spec 068 measured) without eating the
   wrapping driver's context budget.
3. **Capability-set-hash granularity.** Hash by verb names only, or
   by verb names + signatures? **Recommend**: names + signatures — a
   signature change is a wire-shape change (Spec 019) and should
   invalidate the cache.
