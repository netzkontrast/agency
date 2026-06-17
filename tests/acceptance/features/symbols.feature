Feature: symbols capability — token-efficient symbol compression (Spec 300)
  Decidable phrase<->symbol substitution that compresses prose and expands it back.

  Background:
    Given a fresh agency engine in code-mode
    And a confirmed intent

  Scenario: the legend maps phrases to symbols
    When I read the symbols legend
    Then the legend maps "because" and "therefore"

  Scenario: compress substitutes phrases and reports reduction
    When I compress "the tests failed therefore the build is critical"
    Then the compressed text contains the failed and therefore symbols
    And the compression reports a positive token reduction

  Scenario: expand restores symbols to prose
    When I expand a symbol-dense status line
    Then the expanded text contains the words for the symbols
