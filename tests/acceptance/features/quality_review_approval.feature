Feature: subagent judgment + final human-approval elicit (Spec 380 develop.review)

  develop.review (INTERACTIVE) runs the judgment pass — fulfilled by a SUBAGENT,
  no external LLM — then makes a FINAL ELICIT for the human's approval before the
  LLM-proposed judgment findings are accepted. Approve folds them in; reject (or
  no elicit-capable host) drops them, leaving the decidable findings intact. With
  no backend at all it returns a "subagent" delegate envelope for the host to
  fulfil and resume. (The headless analyze.review never pauses — covered by
  quality_judgment.feature.)

  Background:
    Given an engine and confirmed intent

  Scenario: an approved judgment finding is folded into the review
    Given a fixture file and a host that will approve
    When develop.review runs with a subagent judgment reply
    Then the review includes the approved judgment risk_code
    And the decidable finding is still present
    And the judgment is recorded as approved

  Scenario: a rejected judgment finding is dropped, the decidable finding stands
    Given a fixture file and a host that will reject
    When develop.review runs with a subagent judgment reply
    Then the review excludes the judgment risk_code
    And the decidable finding is still present
    And the judgment is recorded as not approved

  Scenario: with no backend, develop.review delegates to a subagent
    Given a fixture file and no inference backend
    When develop.review runs with no completion
    Then it returns a delegate envelope hinting "subagent"
