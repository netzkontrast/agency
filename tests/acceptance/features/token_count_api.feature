Feature: TokenCounter typed result + cache + band agreement (Spec 201)
  Spec 082 already ships the authoritative `messages.count_tokens` backend
  (preferred when ANTHROPIC_API_KEY + the anthropic SDK are present, tiktoken
  /proxy fallbacks). Spec 201 adds the typed `CountResult` return, a
  per-(content, model) cache (so Spec 146's prefix budget is cheap to recompute),
  and the band-agreement invariant between the API and tiktoken counts.

  # ── typed CountResult ──────────────────────────────────────────────────────

  Scenario: count_result returns the typed shape
    Given a proxy-backed token counter
    When I count_result "hello world budget" against "claude-opus-4-8"
    Then the result tokens are positive
    And the result backend is "proxy"
    And the result model is "claude-opus-4-8"
    And the result is not cached

  Scenario: empty text counts zero
    Given a proxy-backed token counter
    When I count_result empty text against "claude-opus-4-8"
    Then the result tokens are zero

  # ── cache idempotence (rule 8) ─────────────────────────────────────────────

  Scenario: the second count of the same content+model is cached and equal
    Given a proxy-backed token counter
    When I count_result "the same content" against "claude-opus-4-8" twice
    Then the second result is cached
    And both results have equal tokens

  Scenario: the cache is keyed by model
    Given a proxy-backed token counter
    When I count_result "shared text" against "claude-opus-4-8"
    And I count_result "shared text" against "claude-haiku-4-5"
    Then the second model's result is not cached

  # ── band agreement (named thresholds) ──────────────────────────────────────

  Scenario: counts within the band agree, outside the band disagree
    Given the band thresholds 0.80 and 1.30
    Then 100 against 100 is within the band
    And 130 against 100 is within the band
    And 80 against 100 is within the band
    And 131 against 100 is outside the band
    And 79 against 100 is outside the band
    And 5 against 0 is within the band
