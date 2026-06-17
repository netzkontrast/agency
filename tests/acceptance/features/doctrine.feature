Feature: doctrine capability — queryable engineering principles + behavioral rules (Spec 303)
  doctrine makes agency's behavioral doctrine machine-queryable + citable: the
  engineering-principles roster, priority-ranked behavioral rules, a conflict-
  resolution hierarchy (safety > correctness > maintainability > speed), and an
  auditable DoctrineCitation when a principle drives an action.

  Background:
    Given a fresh agency engine in code-mode
    And a confirmed intent

  Scenario: principles returns the engineering-principles roster
    When I ask doctrine.principles
    Then the principles roster includes "SOLID"

  Scenario: rules filters by priority
    When I ask doctrine.rules with priority "critical"
    Then every returned rule has priority "critical"
    And at least one critical rule is returned

  Scenario: resolve picks the higher-priority concern by the conflict hierarchy
    When I ask doctrine.resolve between "speed" and "safety"
    Then resolve names "safety" the winner

  Scenario: cite records a DoctrineCitation serving the intent
    When I cite the "SOLID" principle
    Then the citation carries an id
    And a DoctrineCitation for "SOLID" serves the confirmed intent

  Scenario: cite rejects an unknown principle by naming it
    When I cite the "nonsense" principle
    Then the citation result carries an error

  Scenario: a gate adjudicates a conflict by consulting doctrine.resolve
    When I adjudicate a gate between "ship fast" and "data integrity"
    Then the gate adjudication names the safety concern the winner
    And a doctrine.resolve invocation serves the confirmed intent
