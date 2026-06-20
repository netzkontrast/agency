Feature: Lifecycle management discipline
  Scenario: the discipline walks the whole pillar over existing reads
    Given an open Lifecycle in state "input-required"
    When I walk the lifecycle-management discipline
    Then phase 1 surveys them via manage + lifecycle.find

  Scenario: resume re-enters a paused lifecycle at its phase
    Given a Lifecycle in "input-required" recorded at phase "implement"
    When I call lifecycle.resume(lid)
    Then it moves to "working" and returns resume_from="implement"

  Scenario: resume refuses a non-resumable state
    Given an open Lifecycle in state "completed"
    When I call lifecycle.resume(lid)
    Then it raises (only input-required | auth-required are resumable)
