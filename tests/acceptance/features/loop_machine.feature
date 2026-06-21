Feature: The loop machine — Spec 366 (looper port on the lifecycle spine)
  The looper port registers a "loop" state machine in machines.json (the Spec 345
  data-seam); its in-session runtime is this machine walked via the pillar
  (ctx.lifecycle.open(machine="loop") / move). No capability — just a machine.

  Background:
    Given a fresh agency engine in code-mode
    And a confirmed intent

  Scenario: the loop machine opens in planning
    When I open a "loop" lifecycle
    Then its state is "planning"

  Scenario: the happy path walks planning to completed through both gates
    When I open a "loop" lifecycle
    And I move it to "plan_gate"
    And I move it to "delivering"
    And I move it to "delivery_gate"
    And I move it to "completed"
    Then its state is "completed"

  Scenario: the plan gate revises back to planning
    When I open a "loop" lifecycle
    And I move it to "plan_gate"
    Then moving it to "planning" succeeds

  Scenario: the delivery gate revises back to delivering
    When I open a "loop" lifecycle
    And I move it to "plan_gate"
    And I move it to "delivering"
    And I move it to "delivery_gate"
    Then moving it to "delivering" succeeds

  Scenario: skipping the plan gate is illegal
    When I open a "loop" lifecycle
    Then moving it to "completed" raises IllegalTransition

  Scenario: the loop terminals are completed, failed, canceled
    Then the "loop" machine has terminals "completed,failed,canceled"
