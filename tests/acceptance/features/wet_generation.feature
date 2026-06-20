Feature: Use-case model selection + OpenRouter-first generation (Spec 352)
  A use-case-tagged, priority-ordered registry of free OpenRouter models drives
  generation. Plain-text wet generation routes through OpenRouter free models
  when OPENROUTER_API_KEY is set (the owner directive); Anthropic keeps an
  explicit per-call escape. All selection logic is network-free.

  # ── the model registry ─────────────────────────────────────────────────────

  Scenario: the built-in registry is well-formed
    Given the built-in model registry
    Then every model id ends with ":free"
    And every model declares at least one use-case

  Scenario: select_model picks the top-priority model for a use-case
    When I select a model for use-case "reasoning"
    Then the chosen model declares the "reasoning" use-case
    And the chosen model id ends with ":free"

  Scenario: select_model skips models absent from the live catalogue
    Given the top reasoning model is not live-available
    When I select a model for use-case "reasoning" against the live catalogue
    Then the chosen model is a different live reasoning model

  Scenario: an unknown use-case falls back to a general model
    When I select a model for use-case "completely-unknown-usecase"
    Then the chosen model declares the "general" use-case

  Scenario: a config models block overrides the built-in registry
    Given a config registry mapping use-case "prose" to "x/custom-model:free"
    When I select a model for use-case "prose" from the config registry
    Then the chosen model is "x/custom-model:free"

  Scenario: select_model rejects a non-free model override
    When I select with an explicit non-free model "openai/gpt-4o"
    Then a ValueError is raised about a free model

  # ── the single plain-text generator path ───────────────────────────────────

  Scenario: OpenRouter wins for plain text even when both keys are set
    Given OPENROUTER_API_KEY and ANTHROPIC_API_KEY are both set
    When I select the text generator
    Then the generator name is "llm"

  Scenario: require anthropic forces the anthropic generator
    Given OPENROUTER_API_KEY and ANTHROPIC_API_KEY are both set
    When I select the text generator requiring "anthropic"
    Then the generator name is "anthropic"

  Scenario: only an OpenRouter key still routes to OpenRouter
    Given only OPENROUTER_API_KEY is set
    When I select the text generator
    Then the generator name is "llm"

  Scenario: neither key raises a typed dependency-missing error
    Given neither generation key is set
    When I select the text generator
    Then a dependency-missing error is raised

  # ── config-file registry (.agency/config.yaml llm.models) ──────────────────

  Scenario: a config file llm.models block builds the registry
    Given a config file with an llm.models block mapping "prose" to "y/cfg:free"
    When I load the registry from that config file
    Then selecting "prose" from that registry yields "y/cfg:free"

  Scenario: an absent config block falls back to the built-in registry
    Given a config file with no llm block
    When I load the registry from that config file
    Then the loaded registry equals the built-in registry

  Scenario: config validation ignores the structured llm.models block
    Given a config file with an llm.models block mapping "prose" to "y/cfg:free"
    When I validate that config file
    Then no issue mentions "llm.models"

  # ── typed generation result ─────────────────────────────────────────────────

  Scenario: generate returns a typed result with a use-case-chosen free model
    Given an LLMClient with a stub OpenRouter client
    When I generate plain text for use-case "prose"
    Then the result backend is "openrouter"
    And the result model declares the "prose" use-case
    And the result model id ends with ":free"

  # ── free-first in the shared host-LLM seam (complete_or_delegate) ───────────

  Scenario: the shared seam routes plain text to a free model when OpenRouter-keyed
    Given OPENROUTER_API_KEY is set in the seam environment
    And a stub LLMClient that generates for use-case "prose"
    When I complete-or-delegate plain text through the seam
    Then the completion stop reason is "openrouter_free"
    And the completion model id ends with ":free"

  Scenario: the shared seam skips free generation for structured output
    Given OPENROUTER_API_KEY is set in the seam environment
    And a stub LLMClient that generates for use-case "prose"
    And a capable anthropic driver
    When I complete-or-delegate with an output schema through the seam
    Then the completion text is from the driver

  Scenario: the shared seam honors require anthropic over free-first
    Given OPENROUTER_API_KEY is set in the seam environment
    And a stub LLMClient that generates for use-case "prose"
    And a capable anthropic driver
    When I complete-or-delegate requiring "anthropic" through the seam
    Then the completion text is from the driver

  Scenario: the shared seam skips free-first when AGENCY_GENERATE pins anthropic
    Given OPENROUTER_API_KEY is set in the seam environment
    And AGENCY_GENERATE pins anthropic in the seam environment
    And a stub LLMClient that generates for use-case "prose"
    And a capable anthropic driver
    When I complete-or-delegate plain text through the seam
    Then the completion text is from the driver

  Scenario: a host completion resume still wins over free-first
    Given OPENROUTER_API_KEY is set in the seam environment
    And a stub LLMClient that generates for use-case "prose"
    When I complete-or-delegate with a host completion through the seam
    Then the completion stop reason is "host_provided"

  Scenario: no OpenRouter key falls through to the delegate envelope
    Given the seam environment has no generation key
    When I complete-or-delegate plain text through the seam
    Then the seam returns a host-delegate envelope
