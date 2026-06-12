---
spec_id: "147"
slug: anthropic-driver-boundary
status: partial
last_updated: 2026-06-10
owner: "@agency"
enhances: "002"
depends_on: ["002", "026", "082", "110", "146", "150"]
vision_goals: [3, 8]
affects:
  - agency/_drivers/_anthropic.py  (NEW)
  - agency/capabilities/thinking/_main.py
  - tests/test_anthropic_driver.py
---

# Spec 147 — Canonical AnthropicDriver boundary

## Why

Spec 002 ships the Boundary/Driver protocol; Spec 026 mentions an
`llm_select` Matcher still pending a Driver. Spec 110 ships eight
critical-thinking methods that "do it in chat — but lossy". The
agency needs ONE canonical `AnthropicDriver` so every verb that needs
LLM inference (thinking, prompt-composition, dogfood-classifier, scene-
writer, sensitivity-reader) wires through the SAME typed surface with
adaptive thinking, `output_config.format`, `stop_reason` handling, and
optional Managed-Agents session bridging.

## Done When

- [ ] **`AnthropicDriver(Boundary)` typed surface** at
      `agency/_drivers/_anthropic.py`:
      ```python
      class AnthropicDriver(Boundary):
          def complete(
              messages: list[dict],
              system: str | list[dict],
              output_schema: dict | None = None,
              effort: Literal["low","medium","high","xhigh","max"] = "high",
              model: str = "claude-opus-4-8",
              cache_control_breakpoints: list[int] | None = None,
          ) -> Result[Completion, DriverError]: ...
          def stream(...) -> Iterator[StreamEvent]: ...
          def count_tokens(messages, model) -> int: ...
          def dispatch_session(agent_id, env_id, kickoff) -> SessionHandle: ...
      ```
      `Completion` = `{text, stop_reason, usage, model, request_id}`.
      `DriverError` is a typed enum (Spec 151 Codes): `REFUSAL`,
      `RATE_LIMITED`, `OVERLOADED`, `BAD_REQUEST`, `TIMEOUT`,
      `AUTH_FAILED`, `NETWORK`.
- [ ] **Defaults from the `claude-api` skill** — `model="claude-opus-4-8"`,
      `thinking={"type":"adaptive"}`, `output_config.format` when
      `output_schema` supplied, **always stream** (`max_tokens` ≥ 16000
      raises ValueError on non-stream per `claude-api` skill guidance).
- [ ] **`refusal` + `pause_turn` + `max_tokens` stop reasons handled**
      — typed `DriverError.REFUSAL` carries `stop_details.category`
      (`"cyber"` | `"bio"` | `"reasoning_extraction"` | None);
      `pause_turn` auto-resumes by re-sending assistant content (claude-
      api skill `shared/tool-use-concepts.md`); never crashes the engine.
- [ ] **Managed-Agents bridge** — `dispatch_session(...)` references a
      **pre-created** Agent (Spec 137 Lock stores `agent_id` +
      `version`; create-once doctrine — claude-api skill
      `shared/managed-agents-core.md` "Agent FIRST, then session — NO
      EXCEPTIONS"). Events stream back as `MonitorEvent`s (Spec 021);
      each `agent.tool_use` / `session.status_idle` / `session.status_terminated`
      becomes a graph node `SERVES` the originating Intent.
- [ ] **`[anthropic]` extra** in `pyproject.toml` (`anthropic>=0.92` for
      `scope_id` support, claude-api skill).
- [ ] **`agency_doctor` reports `anthropic_driver`** =
      `{api_key_present: bool, managed_agents_capable: bool,
      model_id_resolved: str, retention_meets_fable_5: bool}` (Spec 170).
- [ ] **Spec 110 verbs flip** to use this Driver behind `xcap=True`
      feature flag; degrades to scaffold without the extra.
- [ ] **Prompt-cache discipline (Spec 146)** — every `complete` call
      auto-places `cache_control: {type:"ephemeral"}` on the last
      stable message block when the caller provides a frozen system
      prompt prefix; verified by a mocked `usage.cache_read_input_tokens > 0`
      assertion on the second call.
- [ ] **Live test gated on `ANTHROPIC_API_KEY` env var** (pytest mark
      `live_anthropic`); the unmarked test suite mocks the SDK and
      asserts the typed envelope.
- [ ] **TODO row + drift clean.**

## Worked example (Given/When/Then)

```text
Given:  ANTHROPIC_API_KEY set; an Agent persisted via Spec 137 Lock
When:   driver.dispatch_session(agent_id, env_id, "Summarize chapter 1")
Then:   returns SessionHandle{session_id, status: "running"}
        AND emits a MonitorEvent("session_dispatched") SERVES intent
        AND each subsequent agent.* event becomes a graph node

Given:  classifier model returns stop_reason: "refusal", category: "cyber"
When:   driver.complete(...) called
Then:   returns Result.failure(DriverError.REFUSAL{category:"cyber"})
        AND does NOT consume the wrapping verb's retry budget

Given:  caller asks for max_tokens=64000 without stream
When:   driver.complete(max_tokens=64000, stream=False) called
Then:   raises ValueError pointing at the claude-api streaming guidance
```

## Failure modes (Nygard)

| Failure | Driver response |
|---|---|
| `RATE_LIMITED` | retry with exponential backoff; budget per-intent |
| `OVERLOADED` | retry with backoff; max 3 attempts per intent |
| `REFUSAL` | typed error; never retry the same request |
| `TIMEOUT` | typed error; the wrapping verb decides (per claude-api skill: streaming required for `max_tokens > 16K`) |
| `AUTH_FAILED` | typed error; `agency_doctor` hint |
| `NETWORK` | retry up to 4× with backoff (per Git operations doctrine) |
| Fable 5 on ZDR org | typed `BAD_REQUEST{detail:"retention"}` before dispatch |

## Interconnects

- Anchors the **LLM-driver chain** the charter declares.
- Spec 150 (dogfood classifier) is the first non-thinking consumer.
- Spec 146 (output-prefix) is honored on every wrapped call.
- Spec 026 `llm_select` Matcher lands once this ships.
- Spec 137 (canon-locks) stores the persisted Agent ID + version.
- Spec 151 (Codes coverage) supplies `DriverError` enum.
- Spec 256 (refusal fallback) extends with `fallbacks` parameter.
- Spec 263 (Fable 5 extras) extends with Fable-specific surface.
- Spec 170 (doctor) is the readiness report consumer.

## Open questions

1. **Where does the Agent config YAML live?** **Recommend**: vendored
   `agency/_drivers/agents/<purpose>.agent.yaml` per the `ant` CLI
   pattern; CI applies via `ant beta:agents update` (claude-api skill
   `shared/anthropic-cli.md`).
2. **Vault credential storage?** **Recommend**: Spec 137 Lock with
   `topic="vault-id"` — durable across sessions; credentials never
   enter the agency graph (claude-api skill: credentials are
   write-only).
3. **Backwards compatibility on model deprecation.** When
   `claude-opus-4-8` retires, the default model swaps. **Recommend**:
   the default is a SINGLE config constant; an opt-in
   `pin_model_version=True` lets callers pin for reproducibility.
4. **Session-id correlation across MonitorEvents.** **Recommend**:
   every emitted event carries `session_id` + `agent_id` + `intent_id`
   in its payload so `analyze.graph_query` (Spec 203) can reconstruct
   the full session chain.

## Followup — Implementation Status (2026-06-11, Slice 1)

**Done (Slice 1 — the typed inference surface):**
- `agency/_drivers/_anthropic.py` — `AnthropicDriver` with:
  - `complete(messages, system, output_schema, effort, model, max_tokens)`
    → typed `Completion{text, stop_reason, usage, model, request_id, parsed}`.
    claude-api defaults applied on every request: `model="claude-opus-4-8"`
    (env `AGENCY_ANTHROPIC_MODEL` override), `thinking={"type":"adaptive"}`,
    `output_config.effort`, `output_config.format` (json_schema) when an
    `output_schema` is supplied — `parsed` carries the decoded JSON.
  - `count_tokens(messages, model)` — authoritative API count (never
    tiktoken for Claude; claude-api skill).
  - **Typed `DriverError`** with codes REFUSAL / RATE_LIMITED / OVERLOADED /
    BAD_REQUEST / TIMEOUT / AUTH_FAILED / NETWORK. SDK exceptions map by
    class-name (compile-time SDK-free) with a status-code fallback;
    `stop_reason: "refusal"` raises REFUSAL carrying
    `detail.category` (pre-output refusal semantics per claude-api skill).
  - `max_tokens > 16000` non-streaming guard → BAD_REQUEST pointing at the
    streaming requirement (claude-api skill).
  - `backend()` ("anthropic"/"none", never the key) + `readiness()`
    (`api_key_present` / `model_id_resolved` / `managed_agents_capable`).
  - Lazy SDK import inside `_sdk()` — the module imports with no extra
    installed; missing key raises typed AUTH_FAILED with the fix pointer.
- **Engine wiring**: `Engine(anthropic_driver=...)` kwarg (lazy default,
  test-stubbable); registered as the **`anthropic` Driver** on the Spec-002
  DriverRegistry → verbs reach it via `ctx.get_driver("anthropic")`.
- **`agency_doctor.anthropic_driver`** — the readiness dict (custom-injected
  drivers degrade to `{"backend": "custom"}`).
- **`[anthropic]` extra** in pyproject (the same `anthropic>=0.40` the
  `tokens`/`publish` extras pin).

**Tests:** `tests/test_anthropic_driver.py` — 17 tests, all mocked-SDK
(no network, no extra needed in CI): backend selection ×3, model
default/override, adaptive-thinking+effort request shape, typed
Completion, output_schema → format + parsed, refusal→typed-code with
category, 429/529/401 mapping, keyless AUTH_FAILED, count_tokens,
readiness shape, Slice-2 deferred dispatch_session, engine registration,
doctor readiness. Blast-radius slices green (driver-registry, llm-driver,
naming-audit, doctor/install/bootstrap: 85 passed); `scripts/check-drift`
NO DRIFT.

**Slice 2 (partial) SHIPPED 2026-06-11:**
- `SessionHandle{session_id, status, status_reason, started_at}` —
  frozen dataclass returned by `dispatch_session`.
- `dispatch_session(agent_id, env_id, kickoff) -> SessionHandle` calls
  the SDK shape `client.beta.agents.sessions.create(agent_id=...,
  environment_id=..., kickoff_message=...)`. References a PRE-CREATED
  Agent (create-once doctrine; Spec 137 Lock owns the agent_id +
  version). Rejects empty `agent_id` / `env_id` / `kickoff` with
  `DriverError.BAD_REQUEST`. SDK exceptions map through the same
  `_classify` boundary the `complete()` path uses, so the typed-error
  surface stays uniform.
- `_client_has_sessions_api(client)` capability detector — walks
  `.beta.agents.sessions.create` and returns True when the chain is
  reachable. `readiness().managed_agents_capable` now reflects this
  (was hardcoded False in Slice 1).
- 9 tests added (26 total): typed handle shape, create-once kwargs,
  empty-input rejection (agent_id/env_id/kickoff), status_reason
  surfacing on non-running, frozen-dataclass immutability, readiness
  flip on capable client, readiness=False on bare client, SDK
  exception → DriverError mapping.

**Still (Slice 2.x):**
- MonitorEvent streaming (Spec 021): events from the dispatched session
  (`agent.tool_use`, `session.status_idle`, `session.status_terminated`)
  become graph nodes SERVES'd by the originating Intent.
- `stream()` for >16K-token outputs.
- Spec 110 `thinking.*` verb flips to `run=True` wet paths (Spec 204/226).
- `cache_control` placement on stable prefixes (Spec 146 integration).
- Refusal `fallbacks` parameter + Fable 5 surface (Specs 256/263).

**Open Q resolutions:** Q3 (model deprecation) — default is the single
`_DEFAULT_MODEL` constant + env override; per-call `model=` arg covers
pinning. Q1/Q2/Q4 (Agent YAML home, vault storage, session-id
correlation) are Slice-2 territory, unresolved by design.
