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
> (`:free`-suffix models only), loads `OPENROUTER_API_KEY` / `JULES_API_KEY` from a
> `.env` file via `python-dotenv`, and changes the default model from the paid
> `openai/gpt-4o-mini` to `meta-llama/llama-3.3-70b-instruct:free`.

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
| `agency/_llm.py` | New default (`meta-llama/llama-3.3-70b-instruct:free`), `_FREE_SUFFIX` constant, construction + call-time `:free` enforcement |
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
```

## Followup — Implementation Status (2026-06-19)

**Status: Shipped** — PR #176 (branch `claude/determined-brahmagupta-9eargm`).

### Done
- `_llm.py`: `_DEFAULT_MODEL` changed to `meta-llama/llama-3.3-70b-instruct:free`;
  `_FREE_SUFFIX = ":free"` constant added; `LLMClient.__init__` raises `ValueError`
  on non-free model; `decide()` raises `ValueError` on non-free per-call override.
- `__main__.py`: `from dotenv import load_dotenv; load_dotenv()` at module level.
- `cli.py`: same.
- `pyproject.toml`: `python-dotenv>=1.0` in `[project].dependencies`.

### Still-to-implement
- **Acceptance test suite.** The six Gherkin scenarios above are not yet wired
  into `tests/acceptance/`. A `tests/acceptance/test_openrouter_provider.py` +
  `tests/acceptance/features/openrouter_provider.feature` should cover them
  (mocking network; no real OpenRouter call in CI).
- **`agency_doctor` reporting.** The doctor currently reports `llm_backend`
  as `"openrouter"` or `"none"`. It could add `llm_model` to show the active
  free model, confirming the enforcement is in effect.

### Refinements deferred
- Dynamic free-model discovery: query `GET /api/v1/models` and filter by
  `pricing.prompt == "0"` to validate the configured model is *currently* free
  (the `:free` suffix is reliable but OpenRouter could change the convention).
  Deferred — a startup HTTP call has too high a cost for validation that rarely
  matters in practice.
- Per-call model rotation across multiple free models for rate-limit resilience
  (20 req/min per free model). Deferred until `decide()` is called at a rate
  that hits the limit.
