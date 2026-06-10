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

- [ ] **`agency/_envelope.py`** factors every substrate-tool response
      into `prefix` (frozen — schema header, capability set hash) +
      `body` (volatile — intent-id, timestamps, payload). The Claude
      API caller sets `cache_control` on the prefix; cache hits should
      land on the second call.
- [ ] **`_check_response_prefix` lint rule** (Spec 067 family) flags
      any substrate tool whose prefix interpolates a non-deterministic
      value. Hard error.
- [ ] **`agency_doctor` reports `prefix_stability`** — the cl100k token
      delta of two `agency_welcome` calls 60s apart; ≤ 0 means stable.
- [ ] One test (`test_response_prefix_discipline.py`) hashes the
      prefix of every substrate tool across N=5 invocations and
      asserts byte-identical.
- [ ] TODO row + drift clean.

## Interconnects

- Drives the **output-budget chain** the charter declares.
- Spec 147 (AnthropicDriver) honors the prefix split: every wrapped
  call ships `cache_control: {type:"ephemeral"}` on the prefix.
- Spec 149 (derived docs) consumes `prefix_stability` to flag specs
  whose response shape has rotted.
- Spec 154 (output-overflow) caps body, never prefix.

## Open questions

1. Use `messages.count_tokens(model="claude-opus-4-8")` for measured
   budgets, or stick to local cl100k via Spec 082? **Recommend**: both —
   local for lint speed, API call when `[publish]` extra installed.
