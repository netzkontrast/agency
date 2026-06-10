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

- [ ] **`TokenCounter` gains an `anthropic` backend** behind the
      existing Spec 082 boundary — `messages.count_tokens(model=…)`
      for the model the Driver targets; tiktoken/proxy stay the
      zero-config fallbacks.
- [ ] **The output-budget (Spec 146) uses the best available count** —
      API when present, local otherwise; the band-invariant test (Spec
      082, rule 8) holds across backends.
- [ ] **Fable-5 tokenizer note honored** — the API count reflects the
      ~30% tokenizer delta the `claude-api` skill documents.
- [ ] **`agency_doctor.token_backend` reports the live backend** (Spec
      170).
- [ ] Test: API backend chosen when present (mocked); local fallback
      deterministic; band invariant holds.
- [ ] TODO row + drift clean.

## Interconnects

- **LLM-driver chain** (147) · **output-budget chain** (146).
- Spec 170 (doctor) reports the backend.

## Open questions

1. Cache API counts (they cost a round trip)? **Recommend**: yes,
   per content-hash — counting is deterministic for a given model.
