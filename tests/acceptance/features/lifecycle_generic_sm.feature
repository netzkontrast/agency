Feature: Lifecycle generic state machine — Spec 345
  The lifecycle substrate accepts a named machine parameter and validates
  per-machine transitions. A2A is the default machine (backward-compatible);
  custom machines drive their own state sets.

  Background:
    Given a fresh agency engine in code-mode
    And a confirmed intent

  Scenario: the default machine is a2a and behaviour is unchanged
    When I open a lifecycle with no machine specified
    Then the opened lifecycle machine is "a2a"
    And the opened lifecycle state is "submitted"

  Scenario: a custom machine drives its own states
    Given a registered machine "pipeline" with states ["queued","running","shipped"] and initial "queued"
    When I open a lifecycle with machine "pipeline"
    Then the opened lifecycle state is "queued"
    And moving "pipeline" lifecycle to "running" succeeds
    And moving "pipeline" lifecycle to "shipped" from "queued" raises IllegalTransition

  Scenario: a parameterization is just a derived machine
    When I open a lifecycle with machine "remote-async"
    Then the opened lifecycle state is "submitted"
    And moving "remote-async" lifecycle to "working" succeeds
    And moving "remote-async" lifecycle to "completed" from "working" raises IllegalTransition

  Scenario: the per-machine floor rejects an orphaned state at load
    Then resolving a machine with an orphaned terminal state raises

  Scenario: the ontology accepts any registered machine's state
    Given a registered machine "pipeline" with states ["queued","running","shipped"] and initial "queued"
    Then recording a Lifecycle with state "shipped" and machine "pipeline" passes ontology validation
