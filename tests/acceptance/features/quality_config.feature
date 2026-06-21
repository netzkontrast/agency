Feature: quality config block — tunability + validation (Spec 381 §2)

  The quality config (disable / focus / severity / ignore / strictness) tunes the
  bar per project. Findings are filtered before scoring; validation is surfaced,
  never fatal: focus AND disable together is ignored with a note; an unknown
  strictness falls back to balanced.

  Background:
    Given an engine and confirmed intent

  Scenario: disable removes a risk from the score
    Given findings of one R1 critical and one R2 warning
    When I score under "balanced" with config disabling "R1"
    Then only 1 finding is scored
    And the score is 95

  Scenario: focus evaluates only the listed risks
    Given findings of one R1 critical and one R2 warning
    When I score under "balanced" with config focusing on "R2"
    Then only 1 finding is scored
    And the score is 95

  Scenario: focus and disable together is a config error
    Given findings of one R1 critical and one R2 warning
    When I score with config setting both focus and disable
    Then both findings are scored
    And the config notes report the focus-and-disable conflict

  Scenario: strictness in config selects the preset
    Given findings of one R1 critical and one R2 warning
    When I score with config strictness "strict" and no explicit preset
    Then the preset used is "strict"
