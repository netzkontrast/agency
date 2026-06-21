---
spec_id: "082"
slug: count-tokens-budget
status: shipped
state: done
last_updated: 2026-06-06
owner: "@agency"
depends_on: ["023"]   # the token-budget gate this corrects
research_first: false
domain: capability
wave: 5
---

# Spec 082 — Real token counting for the budget gate (count_tokens, not tiktoken)

## Why

The token-economy doctrine (Spec 023 budget gate, Spec 067/074 lints) measures token
cost with **tiktoken cl100k** — OpenAI's tokenizer. The Anthropic `claude-api` skill
states this directly: *"Do not use tiktoken. It undercounts Claude tokens by ~15–20%
on typical text, and by much more on code."* So the gate at the heart of the
token-economy is calibrated against the wrong tokenizer (graph reflection
`reflection:d46efd50`). The authoritative source is
`POST /v1/messages/count_tokens` (model-specific).

## Design

1. **Token-count boundary.** A stubbable `TokenCounter` injected like the `runner` /
   `jules_client` boundaries: `count(text, model) -> int`. Default impl calls the
   Anthropic SDK `client.messages.count_tokens`; offline/no-key fallback is the
   existing char/4 proxy (so tests + air-gapped runs still work). `agency_doctor`
   reports the live backend (real vs proxy), mirroring the embedder pattern.
2. **Wire it into the gate.** Spec 023's budget test + the Spec 067 token-economy
   lints call the boundary instead of importing tiktoken directly. Genuine **tunable
   budgets** (rule 8) stay documented config; only the MEASUREMENT changes.
3. **Optional extra.** `pip install -e .[tokens]` pulls the Anthropic SDK; absent it,
   the proxy is used — no hard dependency added to the core install.

## Done When

- [ ] `TokenCounter` boundary (real `count_tokens` + proxy fallback), injected on the
  engine; `agency_doctor` surfaces the live backend.
- [ ] Spec 023 budget gate + token-economy lints measure via the boundary; the
  test asserts an INVARIANT (proxy ≤ real within a band on a known sample), not a
  pinned tiktoken number (rule 8).
- [ ] `pyproject` `[tokens]` extra + CI install line + drift tag updated.
- [ ] Tests green (proxy path in CI; real path behind a key-gated marker);
  `check-drift` clean.

## Spec-panel critique

- **Doctrine (rule 8 — no hardcoded values):** good — this REPLACES a frozen-wrong
  number with a live-derived one; assert the proxy/real RELATIONSHIP, not a constant.
- **CI hermeticity:** CI has no API key → the real path can't run in CI. *Accepted:
  default to proxy when no key; gate the real-count test behind a `tokens` marker +
  key, like the BGE/e2e pattern.*
- **Cost:** `count_tokens` is a network call — don't call it per-lint-line. *Accepted:
  batch/aggregate; the gate counts a payload once, not per token.*
- **Skeptic:** is the 15–20% error material to the gate's pass/fail? *Yes for the
  payload-byte/name-token budgets near their thresholds — a 15% undercount can pass a
  payload that's actually over. Worth fixing.*

**Verdict:** APPROVE — proxy-default + key-gated real path + invariant assertions.

## Followup — Implementation Status (2026-06-06)

**Verdict:** Shipped (boundary + centralization + doctor; real-count tier opt-in).

- **`agency/_tokens.py`** — `TokenCounter` (`backend` + `count(text, model)`, never
  raises → degrades to proxy) + `resolve_token_counter()` with tiers **count_tokens**
  (Anthropic SDK + `ANTHROPIC_API_KEY`) → **tiktoken** → **proxy** (`len//4`).
  `AGENCY_TOKENS=proxy|tiktoken` pins a tier (hermetic CI). Module-level
  `count_tokens()` over a cached default.
- **Centralized** the duplicated `tiktoken-else-char//4` helper (a derivability-audit
  catch) — `document/_explain`, `document/_index_repo`, `dogfood` now route through
  the ONE boundary; identical results in CI (tiktoken tier), upgraded when keyed.
- **Engine** exposes `token_counter` (injectable/stubbable); **`agency_doctor`** reports
  `token_backend` so a silent proxy fallback is visible.
- **`[tokens]` extra** (anthropic SDK); optional — CI/offline use tiktoken/proxy.
- **Tests** — `tests/test_token_counter.py` (7): tier selection, injected real counter,
  never-raises fallback, the proxy↔tiktoken **band invariant** (rule 8 — not a pinned
  number), engine exposure. `test_token_budget` + all document/dogfood suites green
  (behaviour-preserving). Full suite green; `check-drift` clean.
- **Deferred:** wire the real `count_tokens` into the Spec 067 lints behind a key-gated
  marker (CI has no key); migrate the remaining `plugin` inline counter.
