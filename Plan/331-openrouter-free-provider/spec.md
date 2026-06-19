---
spec_id: "331"
slug: openrouter-free-provider
status: Shipped
last_updated: 2026-06-19
owner: "@agency"
vision_goals: [1, 3]
depends_on: ["092", "002"]
domain: drivers / configuration
wave: operational
---

# Spec 331 — OpenRouter free-tier provider & dotenv configuration

> Hardens the Spec-092-G3 `LLMClient` boundary: pins it to OpenRouter's free tier
> (`:free`-suffix models only), adds live free-model discovery
> (`AGENCY_LLM_MODEL=auto` + `list_free_models()` / `resolve_model()`), loads
> `OPENROUTER_API_KEY` / `JULES_API_KEY` from a `.env` file via `python-dotenv`,
> changes the default model from the paid `openai/gpt-4o-mini` to
> `meta-llama/llama-3.3-70b-instruct:free`, and wires an optional S12 LLM
> tie-breaker into `delegate.dispatch_decision()`.

## Why

Spec 092 G3 introduced the `llm` Driver as an OpenRouter HTTP boundary for
constrained classification (intent `llm_select` Matcher, pressure-test deciders).
Two operational frictions surfaced during deployment:

1. **Cost exposure.** The default model (`openai/gpt-4o-mini`) and any
   `AGENCY_LLM_MODEL` override silently incur per-token charges. For a
   classification-only driver that makes tiny (<64-token) decisions, paid models
   are never warranted — OpenRouter's free tier (models with the `:free` suffix)
   is sufficient and zero-cost.

2. **Key management ergonomics.** `OPENROUTER_API_KEY` and `JULES_API_KEY` are
   API credentials that should live in a `.env` file alongside the project, not
   hand-exported in the shell on every session. Operators (plugin marketplace
   users, local developers, CI pipelines) all benefit from `.env`-backed config.

Neither is a capability change — the engine behaviour is identical — but without
these guardrails a misconfigured `AGENCY_LLM_MODEL` silently bills the operator,
and a missing shell-export silently disables the driver.

## Design

### Free-only enforcement (`agency/_llm.py`)

OpenRouter free models carry a `:free` suffix in their model ID
(`meta-llama/llama-3.3-70b-instruct:free`, `deepseek/deepseek-r1:free`, etc.).
This is a stable API contract, not a display convention:
the same model without the suffix resolves to a paid route.

The enforcement is **eager** (at `LLMClient.__init__` time) and applies to both
the constructor model and per-call overrides:

```python
_DEFAULT_MODEL = "meta-llama/llama-3.3-70b-instruct:free"
_FREE_SUFFIX = ":free"

class LLMClient:
    def __init__(self, model: str | None = None):
        resolved = model or os.environ.get("AGENCY_LLM_MODEL", _DEFAULT_MODEL)
        if not resolved.endswith(_FREE_SUFFIX):
            raise ValueError(
                f"AGENCY_LLM_MODEL must be a free OpenRouter model "
                f"(model ID must end with '{_FREE_SUFFIX}', got {resolved!r}). "
                f"Browse free models at https://openrouter.ai/models?order=pricing-asc "
                f"or leave AGENCY_LLM_MODEL unset to use the default ({_DEFAULT_MODEL})."
            )
        self.model = resolved
```

The per-call check in `decide()` rejects a non-free model override before the
network is touched:

```python
use_model = model or self.model
if not use_model.endswith(_FREE_SUFFIX):
    raise ValueError(...)
```

**Why fail-fast at construction, not at call time?** A misconfigured model that
slips through until the first `decide()` call may not surface until a user's
production flow runs. Construction-time is cheaper to catch, and the engine
factory (`engine.py:_boundary_defaults`) instantiates `LLMClient()` lazily on
first use — so the error will surface at first driver call, before any network
request is made.

### Default model choice: `meta-llama/llama-3.3-70b-instruct:free`

Selection criteria:
- **Instruction-following quality.** The `decide()` method requires strict JSON
  compliance from a constrained prompt. Llama 3.3 70B consistently follows
  system-prompt instructions and `response_format: json_schema`.
- **Free-tier availability.** As of 2026-06, this model is among the most
  consistently available free models on OpenRouter (not rotated out like
  smaller/experimental variants).
- **Context window.** 128K context — overkill for a 64-token classification
  response, but headroom means no accidental truncation of the option list.

Alternative free models that work (set via `AGENCY_LLM_MODEL`):
- `deepseek/deepseek-r1:free` — strongest reasoning on free tier
- `deepseek/deepseek-chat-v3-0324:free` — fast, well-balanced
- `qwen/qwen3-coder:free` — best for code-oriented decisions (262K context)

### Live free-model discovery (`AGENCY_LLM_MODEL=auto`)

Setting `AGENCY_LLM_MODEL=auto` triggers dynamic model selection at construction
time via two new classmethods on `LLMClient`:

**`list_free_models(api_key=None) -> list[dict]`** — queries
`GET /api/v1/models` (public; optional auth header for authenticated results) and
returns `{id, name, context_length}` for every model whose ID ends with `:free`.
Authentication is opportunistic — the public endpoint returns the full free-model
catalogue without a key, but including the key avoids rate-limiting.

**`resolve_model(api_key=None) -> str`** — walks `_MODEL_PREFERENCE` in order,
returning the first model whose ID appears in the live catalogue. Falls back to
`_DEFAULT_MODEL` when the API is unreachable or no preference matches.

```python
_MODEL_PREFERENCE: list[str] = [
    "deepseek/deepseek-r1:free",          # dominates free-tier traffic (2026)
    "deepseek/deepseek-chat-v3-0324:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "qwen/qwen3-coder:free",
    "google/gemma-3-27b-it:free",
    "mistralai/mistral-7b-instruct:free",
]

class LLMClient:
    def __init__(self, model: str | None = None):
        raw = model or os.environ.get("AGENCY_LLM_MODEL", _DEFAULT_MODEL)
        if raw == "auto":
            resolved = self.resolve_model()  # live catalogue walk
        else:
            resolved = raw
        if not resolved.endswith(_FREE_SUFFIX):
            raise ValueError(...)
        self.model = resolved
```

**Why `_MODEL_PREFERENCE` not live-usage-ranked?** The OpenRouter
`/api/v1/models` endpoint does not expose per-model traffic or usage statistics.
The preference list is ranked by community usage research (DeepSeek R1 leads
OpenRouter free-tier traffic as of 2026-06) — a reasonable stable proxy that
avoids an extra HTTP round-trip.

**Fallback chain:** `auto` → live catalogue walk → first preference hit →
`_DEFAULT_MODEL` (if network fails or no preference matches). No exception is
raised when the catalogue is unreachable — the fallback ensures the driver stays
operational in air-gapped or rate-limited environments.

### S12 LLM tie-breaker in `delegate.dispatch_decision()`

`dispatch_decision()` gains three optional parameters that wire the `llm` Driver
as an optional post-heuristic validator (S12):

```python
def dispatch_decision(
    self,
    # ... existing S1–S11 signals ...
    use_llm: bool = False,                    # S12 — consult LLMClient after heuristic
    task_description: str = "",               # plain-text fed to decide()
    llm_confidence_threshold: float = 0.75,  # minimum confidence to accept LLM override
) -> dict:
```

When `use_llm=True` and the 11-signal heuristic produces a driver, the helper
`_llm_dispatch_signal()` is called:

1. Fetches the `llm` driver via `ctx.get_driver("llm")`.  Silently skips
   (returns `None`, heuristic stands) when the driver is unavailable
   (`DriverMissing`) or `OPENROUTER_API_KEY` is unset.
2. Constructs a prompt from `task_description` and `signals_fired`, then calls
   `llm.decide(prompt, options=["local", "jules", "inline"])`.
3. If `result["confidence"] >= llm_confidence_threshold` AND
   `result["choice"] != heuristic_driver`, records `S12:llm_override=<choice>`
   and replaces the driver.
4. Otherwise records `S12:llm_confirms=<choice>` and leaves the heuristic
   decision intact.
5. Any exception from `decide()` is swallowed — the heuristic always wins on
   failure.

This keeps the S12 signal strictly additive: existing callers passing no LLM
parameters get identical behaviour. The threshold default of 0.75 means the LLM
must be fairly confident before overriding a deterministic signal.

### `python-dotenv` integration (`agency/__main__.py`, `agency/cli.py`)

`load_dotenv()` is called at module import time in both entry points:

```python
# agency/__main__.py  (MCP server entry)
from dotenv import load_dotenv
load_dotenv()  # populate OPENROUTER_API_KEY / JULES_API_KEY from .env

# agency/cli.py  (bash CLI entry)
from dotenv import load_dotenv
load_dotenv()  # same, before any lazy driver reads
```

**Call site rationale.** `load_dotenv()` must fire before any `os.environ.get()`
read. The drivers read lazily (only when a verb invokes them), but a future
`_llm.py` or `jules/api.py` refactor might read at import time. Placing the call
at entry-point import removes any order dependency.

**`load_dotenv()` is a no-op when no `.env` is present.** Containerised and
cloud deployments that inject env vars directly are unaffected. The `.env` file is
never required — it is an opt-in convenience.

**`.env` file location.** `load_dotenv()` without arguments searches upward from
the current working directory (python-dotenv default). For the MCP server
(`agency-mcp`), the working directory is set to `${CLAUDE_PROJECT_DIR}` in the
`.mcp.json` config, so the project root's `.env` is found automatically.

### `pyproject.toml` dependency

```toml
"python-dotenv>=1.0",
```

Added to the core `[project].dependencies` list (not an optional extra). Dotenv
loading is a zero-cost startup concern that benefits all deployment patterns;
making it optional would require conditional import guards that complicate the
entry points.

## Affected files

| File | Change |
|---|---|
| `agency/_llm.py` | New default (`meta-llama/llama-3.3-70b-instruct:free`), `_FREE_SUFFIX` / `_MODELS_URL` constants, `_MODEL_PREFERENCE` list, `AGENCY_LLM_MODEL=auto` handling, `list_free_models()` + `resolve_model()` classmethods, construction + call-time `:free` enforcement |
| `agency/capabilities/delegate/_main.py` | `use_llm` / `task_description` / `llm_confidence_threshold` params on `dispatch_decision()`; `_llm_dispatch_signal()` helper |
| `agency/__main__.py` | `load_dotenv()` call at module level |
| `agency/cli.py` | `load_dotenv()` call at module level |
| `pyproject.toml` | `python-dotenv>=1.0` in core deps |

## What stays unchanged

- `JULES_API_KEY` reading in `agency/capabilities/jules/api.py` — `_api_key()`
  still reads `os.environ.get("JULES_API_KEY", "")`. The dotenv loading upstream
  populates `os.environ` before this is called; no change needed here.
- `LLMClient.backend()` reporting — still returns `"openrouter"` vs `"none"`.
- `agency_doctor` health reporting — no change; it checks key presence, not value.
- The `response_format: json_schema` strict schema and tolerant `_parse()` — no
  change; the free model default handles it correctly.

## Acceptance scenarios

```gherkin
Feature: OpenRouter free-provider enforcement

  Scenario: Default model is free
    Given LLMClient is constructed with no model argument
    And AGENCY_LLM_MODEL is unset
    Then the client's model is "meta-llama/llama-3.3-70b-instruct:free"

  Scenario: Non-free model raises at construction
    When LLMClient is constructed with model "openai/gpt-4o-mini"
    Then a ValueError is raised
    And the error mentions ":free" suffix and the default model name

  Scenario: Custom free model is accepted
    When LLMClient is constructed with model "deepseek/deepseek-r1:free"
    Then no exception is raised
    And the client's model is "deepseek/deepseek-r1:free"

  Scenario: Non-free per-call override is rejected
    Given a LLMClient with the default model
    When decide() is called with model="openai/gpt-4o-mini"
    Then a ValueError is raised before any network call

  Scenario: .env key is loaded by entry point
    Given OPENROUTER_API_KEY is not in os.environ
    And a .env file in the project root sets OPENROUTER_API_KEY
    When the MCP server entry point (agency/__main__.py) is imported
    Then os.environ["OPENROUTER_API_KEY"] is set

  Scenario: load_dotenv is a no-op when no .env exists
    Given no .env file is present
    When the entry point is imported
    Then no exception is raised
    And existing os.environ values are unchanged

Feature: Free-model auto-discovery

  Scenario: auto mode picks most-preferred available model
    Given AGENCY_LLM_MODEL is set to "auto"
    And the OpenRouter catalogue contains "deepseek/deepseek-r1:free"
    When LLMClient is constructed
    Then the client's model is "deepseek/deepseek-r1:free"

  Scenario: auto mode falls back to default when catalogue unreachable
    Given AGENCY_LLM_MODEL is set to "auto"
    And the OpenRouter /api/v1/models endpoint is unreachable
    When LLMClient is constructed
    Then no exception is raised
    And the client's model is "meta-llama/llama-3.3-70b-instruct:free"

  Scenario: list_free_models returns only :free-suffixed models
    When list_free_models() is called
    Then every returned model's id ends with ":free"

Feature: S12 LLM dispatch tie-breaker

  Scenario: use_llm=False leaves heuristic result unchanged
    Given dispatch_decision() is called with use_llm=False
    Then no LLM driver is consulted
    And the returned driver equals the 11-signal heuristic result

  Scenario: LLM overrides heuristic when confident
    Given dispatch_decision() is called with use_llm=True and task_description="..."
    And the 11-signal heuristic picks "local"
    And the LLM returns choice="jules" with confidence=0.9
    And llm_confidence_threshold is 0.75
    Then the returned driver is "jules"
    And signals contains "S12:llm_override=jules"

  Scenario: LLM confirms heuristic when low confidence
    Given dispatch_decision() is called with use_llm=True
    And the 11-signal heuristic picks "jules"
    And the LLM returns choice="local" with confidence=0.6
    And llm_confidence_threshold is 0.75
    Then the returned driver is "jules"
    And signals contains "S12:llm_confirms=jules"

  Scenario: LLM driver unavailable silently skips S12
    Given dispatch_decision() is called with use_llm=True
    And OPENROUTER_API_KEY is not set
    Then no exception is raised
    And the returned driver equals the 11-signal heuristic result
```

## Followup — Implementation Status (2026-06-19)

**Status: Shipped** — PR #176 (branch `claude/determined-brahmagupta-9eargm`).

### Done
- `_llm.py`: `_DEFAULT_MODEL` changed to `meta-llama/llama-3.3-70b-instruct:free`;
  `_FREE_SUFFIX = ":free"` / `_MODELS_URL` constants added; `LLMClient.__init__`
  raises `ValueError` on non-free model; `decide()` raises `ValueError` on non-free
  per-call override; `AGENCY_LLM_MODEL=auto` triggers `resolve_model()`.
- `_llm.py`: `list_free_models()` queries `GET /api/v1/models`, filters to `:free`
  IDs, returns `{id, name, context_length}` list.
- `_llm.py`: `resolve_model()` walks `_MODEL_PREFERENCE` against live catalogue;
  falls back to `_DEFAULT_MODEL` on network failure or no match.
- `_llm.py`: `_MODEL_PREFERENCE` list ranked by community usage (DeepSeek R1 first).
- `capabilities/delegate/_main.py`: `dispatch_decision()` gains `use_llm`,
  `task_description`, `llm_confidence_threshold` params; `_llm_dispatch_signal()`
  helper implements S12 — fetches `llm` driver, calls `decide()`, records
  `S12:llm_override=<x>` or `S12:llm_confirms=<x>` in signals; silently no-ops
  when driver unavailable or `decide()` raises.
- `__main__.py`: `from dotenv import load_dotenv; load_dotenv()` at module level.
- `cli.py`: same.
- `pyproject.toml`: `python-dotenv>=1.0` in `[project].dependencies`.

### Still-to-implement
- **Acceptance test suite.** The thirteen Gherkin scenarios above are not yet wired
  into `tests/acceptance/`. `tests/acceptance/test_openrouter_provider.py` +
  `tests/acceptance/features/openrouter_provider.feature` should cover the
  enforcement and dotenv scenarios (mocking network; no real OpenRouter call in CI).
  `tests/acceptance/test_delegate_s12.py` should cover the S12 dispatch scenarios
  (mocking the `llm` driver's `decide()` return).
- **`agency_doctor` reporting.** The doctor currently reports `llm_backend`
  as `"openrouter"` or `"none"`. It could add `llm_model` to show the active
  free model, confirming the enforcement is in effect.

### Refinements deferred
- Per-call model rotation across multiple free models for rate-limit resilience
  (20 req/min per free model on OpenRouter free tier). Deferred until `decide()`
  is called at a rate that hits the limit.
