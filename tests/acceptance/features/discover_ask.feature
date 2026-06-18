Feature: discover.ask — the well-formed AskUser question primitive (Spec 310)
  One place the well-formed-question rules live: 2-4 options, recommended-first,
  header <= 12 chars, multiSelect only on independent axes, and every option
  DERIVED from supplied evidence (referential provenance) — recorded as a
  ClarificationQuestion the discovery can replay. Read-only beyond that node.

  Background:
    Given a fresh agency engine in code-mode
    And a confirmed intent

  Scenario: ask clamps options, recommends one, derives every option from evidence
    When I ask with 9 requested options over 5 context items
    Then the ask payload has between 2 and 4 options
    And exactly the first option is marked recommended
    And every option provenance resolves to a supplied context item
    And the ask payload header is at most 12 characters

  Scenario: ask refuses a manufactured option (referential oracle, not word-overlap)
    When a manufactured option with unresolvable provenance is derived
    Then the ask is rejected as an invalid argument

  Scenario: ask is read-only — records one ClarificationQuestion, no CLARIFIES edge
    When I ask with 3 requested options over 5 context items
    Then exactly one ClarificationQuestion serves the intent
    And no CLARIFIES edge is written to the intent

  Scenario: multiSelect is a function of the flag
    When I ask for independent axes
    Then the ask payload allows multiple selections

  Scenario: the emit then fold round-trip transitions the question to answered
    When I ask with 3 requested options over 5 context items
    And the caller folds an answer for that question
    Then the ClarificationQuestion is answered
    And folding an unknown question id raises
