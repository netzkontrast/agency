Feature: develop.maintain — the autolearning recurring-maintenance loop
  The 'Agency Steward' maintenance discipline lives as a verb, not a fragile
  external prompt: each call returns the hardened phase plan + an evidence-grounded
  candidate shortlist computed from the LIVE graph, and records a MaintenanceRun
  linked PRECEDES from the prior run — so the task learns across scheduled runs
  (the run chain + the reflection backlog are its memory).

  Background:
    Given a fresh agency engine
    And a confirmed intent

  Scenario: maintain returns the hardened steward phases grounded in live signals
    When I invoke develop maintain
    Then maintain returns the seven steward phases
    And maintain returns live-graph signals
    And maintain records a maintenance run

  Scenario: maintain learns from the prior run via the PRECEDES chain
    When I invoke develop maintain twice
    Then the second run links PRECEDES from the first
    And the second run reports the first as its prior
