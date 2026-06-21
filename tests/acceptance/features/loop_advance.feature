Feature: The loop walk reducer — Spec 366 advance (looper run() on the spine)
  advance() is the sole in-session walk step: read the state, run the gate
  (criteria 364 + council verdict 365), ask control_evaluate, then
  lifecycle.move. pass advances; revise loops back and counts; a denied guard
  fails the loop carrying the stop_reason. Status derives from the graph.

  Background:
    Given a fresh agency engine in code-mode

  Scenario: a clean plan advances to delivering
    Given an open loop with a passing programmatic criterion
    When I advance from planning to the plan gate
    And I advance the clean plan gate
    Then the loop state is "delivering"

  Scenario: a revise verdict loops back to planning and counts a revision
    Given an open loop with a judge criterion
    When I advance from planning to the plan gate
    And I advance the plan gate with a revise verdict
    Then the loop state is "planning"
    And the revision count is 1

  Scenario: max_revisions stops the loop
    Given an open loop with a judge criterion and caps max_revisions 2 stall 99
    When the plan gate is revised 2 times
    Then the loop failed with stop_reason "max_revisions"

  Scenario: no-progress stops on a repeated blocker
    Given an open loop with a judge criterion and caps max_revisions 99 stall 2
    When the plan gate is revised 2 times with the same blocker
    Then the loop failed with stop_reason "no_progress"

  Scenario: status and stop conditions are read from the graph
    Given an open loop with a judge criterion and caps max_revisions 99 stall 2
    When the plan gate is revised 2 times with the same blocker
    Then the loop progress reads from the graph and no state.json was written
