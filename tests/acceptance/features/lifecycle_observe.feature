Feature: Lifecycle observe frame — read · find · check · watch (Spec 341)
  The observe half of the CORE.md §3 frame, REUSED on the Memory pillar (manage):
  `read` = manage.lifecycle (a rollup), `find` = manage.list("Lifecycle", where),
  `check` = gate.check (a failed check IS a transition), `watch` = manage.lifecycle_trail
  over the Spec 344 transition events. No new storage, no new event source.

  Background:
    Given a fresh agency engine in code-mode
    And a confirmed intent

  Scenario: read projects one lifecycle's full state
    Given an opened lifecycle moved to "working"
    When I read the lifecycle via manage.lifecycle
    Then the read reports state "working" and the serving intent

  Scenario: find filters live lifecycles by state
    Given a "working" lifecycle and a "completed" lifecycle
    When I list lifecycles in state "working"
    Then exactly 1 lifecycle is returned

  Scenario: check failure is a transition, not a raw update
    Given an opened lifecycle moved to "working"
    When a gate fails on the lifecycle
    Then the lifecycle read reports state "input-required"

  Scenario: watch returns the durable transition trail
    Given an opened lifecycle moved to "working"
    When I move the lifecycle to "completed"
    And I read the transition trail via manage.lifecycle_trail
    Then the trail contains a transition to "completed"
