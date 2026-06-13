Feature: token budget — search results stay within budget (Spec 023 / 082)
  The search verb must return results within the token budget so the discovery
  flow stays token-tight. The token counter resolves through tiktoken or a
  char/4 proxy and is exposed on the engine.

  Background:
    Given a fresh agency engine in code-mode

  Scenario: search for a specific verb stays within the 120-token budget
    When I search for "reflect note" with limit 5
    Then the result token count is at most 120

  Scenario: search for a broader query stays within 120 tokens
    When I search for "dispatch" with limit 5
    Then the result token count is at most 120

  Scenario: wider search stays within the 200-token budget
    When I search for "graph" with limit 8
    Then the result token count is at most 200

  Scenario: the engine exposes a usable token counter
    Given a fresh agency engine in code-mode
    When I inspect the engine token counter
    Then it has a non-empty backend name
    And it returns a positive count for a non-empty string

  Scenario: token counter degrades gracefully when backend fails
    Given a token counter whose backend always raises
    When I count tokens for a 40-character string
    Then the result is the char/4 proxy value of 10
