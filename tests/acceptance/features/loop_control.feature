Feature: Loop termination guards — Spec 366 (the control evaluator)
  The loop machine's termination guards (ported from looper's run-loop.py) are a
  pure evaluator in agency/_loop.py, consulted before each move: max_revisions,
  max_iterations, no_progress, budget. It returns {permit, stop_reason}. This is
  looper's honest-durability promise: a loop always stops.

  Scenario: a fresh loop permits the move
    Given a loop control with max_iterations 12, max_revisions 3, no_progress_stall 2
    When I evaluate control with iterations 0, revisions 0, stalled 0, elapsed 0
    Then the move is permitted

  Scenario: max_revisions stops the loop
    Given a loop control with max_revisions 3
    When I evaluate control with revisions 3
    Then the move is denied with stop_reason "max_revisions"

  Scenario: max_iterations stops the loop
    Given a loop control with max_iterations 12
    When I evaluate control with iterations 12
    Then the move is denied with stop_reason "max_iterations"

  Scenario: a repeated blocker stops as no_progress
    Given a loop control with no_progress_stall 2
    When I evaluate control with stalled 2
    Then the move is denied with stop_reason "no_progress"

  Scenario: a wall-clock budget breach stops the loop
    Given a loop control with wall_clock_min 30
    When I evaluate control with elapsed 31
    Then the move is denied with stop_reason "budget"

  Scenario: budget takes priority over a revision breach
    Given a loop control with max_revisions 3 and wall_clock_min 30
    When I evaluate control with revisions 5 and elapsed 31
    Then the move is denied with stop_reason "budget"
