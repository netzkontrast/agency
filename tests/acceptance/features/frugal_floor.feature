Feature: frugal safety-floor gate (Spec 326 Slice 4)
  The safety floor is a first-class, tested clause — a gate-recordable predicate
  that the rendered discipline never omits the floor at any level but off.

  Scenario: the safety floor is intact across every non-off level
    When I evaluate the frugal safety-floor predicate
    Then the safety-floor predicate passes
    And it checked every non-off level

  Scenario: the predicate catches a stripped floor
    When I evaluate the predicate against a render that drops a floor marker
    Then the safety-floor predicate fails
    And the findings name the dropped marker

  Scenario: the floor predicate records a passing Gate
    Given a confirmed intent
    And an open lifecycle
    When I record the safety-floor predicate as a gate "frugal_safety_floor"
    Then the recorded gate passed
