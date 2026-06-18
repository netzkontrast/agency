Feature: discover.clarify — the ambiguity-resolution loop (Spec 311)
  Finds what is still vague in a draft Intent, asks one targeted question per
  ambiguity (composing discover.ask), folds each answer back bi-temporally
  (intent.amend), and records a CLARIFIES trail — until residual ambiguity drops
  below threshold or a max-rounds budget is hit.

  Background:
    Given a fresh agency engine in code-mode
    And a confirmed intent

  Scenario: the loop resolves ambiguities and exits below threshold
    When I clarify a vague draft with budget 5
    Then the clarify loop exits below threshold
    And the residual ambiguity is zero
    And each round score is non-increasing
    And it resolved in fewer rounds than the budget

  Scenario: one CLARIFIES edge is recorded per round
    When I clarify a vague draft with budget 5
    Then the CLARIFIES edge count equals the round count

  Scenario: each fold-back is bi-temporal keep-both
    When I clarify a vague draft with budget 5
    Then both the original intent and its amended revision are recallable

  Scenario: a tight budget exits by max_rounds
    When I clarify a vague draft with budget 1
    Then the clarify loop exits by max_rounds
    And exactly one round ran
