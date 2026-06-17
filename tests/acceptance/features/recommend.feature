Feature: recommend capability — request → capability routing (Spec 298)
  Given a free-text request, recommend the most suitable agency capability + verb
  by reading the live registry, recorded as provenance.

  Background:
    Given a fresh agency engine in code-mode
    And a confirmed intent

  Scenario: a research request routes to the research capability
    When I ask for a recommendation for "research and gather cited evidence on a question"
    Then a recommendation names the "research" capability
    And the recommendation records a Recommendation node serving the intent

  Scenario: an analysis request routes to the analyze capability
    When I ask for a recommendation for "analyze the code quality and security"
    Then a recommendation names the "analyze" capability

  Scenario: routing reports each capability's graph usage frequency
    Given the "manage" capability has been invoked twice
    When I ask for a recommendation for "create read update or retract a node"
    Then the manage recommendation carries a usage count of at least two
