Feature: Opening a loop — Spec 366 (_loop.open)
  _loop.open mints a Lifecycle on the "loop" machine SERVING the goal Intent and
  records the termination control on the node; it refuses a guard-free loop
  (looper: never emit a loop with no termination guard).

  Background:
    Given a fresh agency engine in code-mode
    And a confirmed intent

  Scenario: opening a loop mints a loop lifecycle in planning with control recorded
    When I open a loop with max_iterations 5 and max_revisions 2
    Then the loop state is "planning"
    And the recorded control has max_iterations 5 and max_revisions 2

  Scenario: opening refuses a termination-guard-free loop
    When I open a guard-free loop
    Then opening is refused
