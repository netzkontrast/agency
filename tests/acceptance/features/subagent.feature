Feature: Subagent capability — subagent-driven development composition
  subagent.develop fans a task out to a child lifecycle, runs a two-stage
  gate (spec-review → quality-review), and marks the child completed only
  when both gates pass (Spec 041).

  Background:
    Given a fresh agency engine in code-mode
    And a confirmed intent

  Scenario: both gates pass — child is marked completed and done is true
    When I dispatch a subagent task with both gates passing
    Then the develop result reports done true
    And the child lifecycle is completed

  Scenario: spec gate fails — done is false and child stays open
    When I dispatch a subagent task with the spec gate failing
    Then the develop result reports done false
    And the spec gate verdict is recorded

  Scenario: both gates pass — quality gate runs and is recorded
    When I dispatch a subagent task with both gates passing
    Then the quality gate verdict is recorded

  # Spec 339b — subagent.develop routes completion through lifecycle.move (not raw memory.update).
  # Proof: move emits a durable lifecycle_transition Event for terminal states (Spec 344);
  # raw memory.update would not.

  Scenario: completed child emits a durable lifecycle transition Event
    When I dispatch a subagent task with both gates passing
    Then a durable lifecycle_transition Event to "completed" exists for the child lifecycle

  Scenario: incomplete child does not emit a completed transition Event
    When I dispatch a subagent task with the spec gate failing
    Then no lifecycle_transition Event to "completed" exists for the child lifecycle
