Feature: Spec 338 — OpenRouter-first wet generation

  Scenario: OpenRouter wins when both keys are set
    Given a driver registry with llm and anthropic drivers registered
    When select_text_generator is called with both keys set in the env
    Then the returned backend name is "llm"
    And the returned driver is the registered llm object

  Scenario: Anthropic fallback when only ANTHROPIC_API_KEY is set
    Given a driver registry with llm and anthropic drivers registered
    When select_text_generator is called with only ANTHROPIC_API_KEY set
    Then the returned backend name is "anthropic"
    And the returned driver is the registered anthropic object

  Scenario: DEPENDENCY_MISSING when neither key is set
    Given a driver registry with llm and anthropic drivers registered
    When select_text_generator is called with no keys set
    Then a RuntimeError is raised mentioning dependency_missing

  Scenario: generate() enforces the :free model suffix
    Given the OPENROUTER_API_KEY is set in the environment
    When LLMClient.generate is called with a non-free model override
    Then a ValueError is raised mentioning the :free requirement

  Scenario: generate() raises when OPENROUTER_API_KEY is absent
    Given the OPENROUTER_API_KEY is absent from the environment
    When LLMClient.generate is called with the default model
    Then a RuntimeError is raised mentioning the missing key

  Scenario: generate() returns GenerationResult via a mocked OpenRouter call
    Given the OPENROUTER_API_KEY is set in the environment
    And httpx.post is mocked to return a valid generation response
    When LLMClient.generate is called with a prompt
    Then the result is a GenerationResult instance
    And the model in the result ends with :free
    And the backend in the result is "openrouter"
