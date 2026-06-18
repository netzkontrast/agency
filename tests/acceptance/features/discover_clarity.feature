Feature: discover.clarity — the Intent readiness score + gate input (Spec 322)
  Scores a captured Intent's clarity as the normalized sum of five independent
  readiness signals, each COMPUTED from the live discovery graph. Read-only — the
  confirm gate reads {score, missing, ready} to refuse work against a vague Intent.

  Background:
    Given a fresh agency engine in code-mode
    And a confirmed intent

  Scenario: a freshly interviewed draft scores low and is not ready
    When I interview and score the resulting draft
    Then the clarity score is between 0 and 1
    And the draft is not ready
    And missing lists the unsatisfied readiness signals

  Scenario: an incomplete interview draft lacks the triple signal
    When I interview vaguely and score the resulting draft
    Then the has_triple signal is false

  Scenario: satisfying signals raises the score and flips ready
    When I interview and score the resulting draft
    And I add a measurable acceptance criterion and a scope boundary to the draft
    And I re-score the draft
    Then the clarity score increased
    And the draft is now ready
    And scoring created no extra acceptance criterion
