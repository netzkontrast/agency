Feature: Frugal embedded in lifecycle — Spec 347
  Frugal becomes a property of how work moves through any state machine:
  a non-removable floor every machine must honour, the stamp every transition
  carries, and a drivable machine in its own right.

  Background:
    Given a fresh agency engine in code-mode
    And a confirmed intent

  Scenario: a machine that skips the floor is rejected at load
    Then a machine whose path to "done" skips the floor gate raises

  Scenario: a floor-honouring machine loads
    Then a machine whose path to "done" passes through the floor gate is accepted

  Scenario: transition events carry the frugal stamp
    When I open an a2a lifecycle and move to "completed"
    Then the durable transition event has a non-empty frugal field

  Scenario: frugal is a drivable machine
    When I open a lifecycle with machine "frugal"
    Then the opened lifecycle state is "assess"
    And I can walk the frugal machine to "done"

  Scenario: the floor definition has a single source (Spec 332)
    When I open an a2a lifecycle and move to "completed"
    Then the frugal field on the event matches frugal_level from Spec 332
