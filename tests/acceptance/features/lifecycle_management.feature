Feature: Lifecycle management discipline — Spec 343
  The capstone: a walkable discipline (delivered phase-by-phase via
  develop.skill_walk) that orchestrates the existing pillar verbs, plus
  lifecycle.resume (the phase/state bridge re-entering a paused lifecycle), and
  the report phase that mirrors the in-flight board to a Spec 292 file peer.

  Scenario: the discipline walks the whole pillar over existing reads
    Given an open Lifecycle in state "input-required"
    When I walk the lifecycle-management discipline
    Then the walk completes through the six named phases
    And a Skill provenance record for the walk exists serving the intent

  Scenario: resume re-enters a paused lifecycle at its phase
    Given a Lifecycle in "input-required" recorded at phase "implement"
    When I call lifecycle.resume(lid)
    Then it moves to "working" and returns resume_from="implement"

  Scenario: resume refuses a non-resumable state
    Given an open Lifecycle in state "completed"
    When I call lifecycle.resume(lid)
    Then it raises (only input-required | auth-required are resumable)

  Scenario: the board renders as a file peer
    Given an open Lifecycle in state "input-required"
    When the report phase mirrors the lifecycle board to a file
    Then lifecycle-board.md is written with the in-flight board
