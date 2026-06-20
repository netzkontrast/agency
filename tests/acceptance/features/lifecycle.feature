Feature: Lifecycle pillar substrate — the open/move/close state machine (Spec 339)
  The Lifecycle pillar's substrate (agency/lifecycle.py) owns the write frame:
  open mints a lifecycle in `submitted`, move is the sole state-shaped writer
  that validates the target state and refuses a no-op, and close drives to a
  terminal state.

  Background:
    Given a fresh agency engine in code-mode
    And a confirmed intent

  Scenario: open mints a lifecycle in submitted
    When I open a lifecycle serving the intent
    Then the opened lifecycle state is "submitted"

  Scenario: move transitions the state
    Given an opened lifecycle
    When I move the lifecycle to "working"
    Then the opened lifecycle state is "working"

  Scenario: move rejects an unknown state
    Given an opened lifecycle
    When I move the lifecycle to an unknown state
    Then the move is rejected

  Scenario: move refuses a no-op transition
    Given an opened lifecycle
    When I move the lifecycle to "working"
    And I move the lifecycle to "working" again
    Then the second move is rejected

  Scenario: close drives to a terminal state
    Given an opened lifecycle
    When I move the lifecycle to "working"
    And I close the lifecycle as "completed"
    Then the opened lifecycle state is "completed"

  # Spec 339a-cont — wire the substrate frame to the engine: ctx.lifecycle
  # delegator, the lifecycle_* substrate tools, and the delegate migration.

  Scenario: open records the parameterization seam
    When I open a remote-async lifecycle serving the intent
    Then the opened lifecycle state is "submitted"
    And the opened lifecycle parameterization is "remote-async"

  Scenario: the lifecycle_open substrate tool mints through the substrate
    Given an opened lifecycle via the lifecycle_open substrate tool
    Then the opened lifecycle state is "submitted"

  Scenario: the lifecycle_move substrate tool transitions through the substrate
    Given an opened lifecycle via the lifecycle_open substrate tool
    When I move the lifecycle to "working" via the lifecycle_move substrate tool
    Then the opened lifecycle state is "working"

  Scenario: delegate fan_out opens children through the lifecycle substrate
    When delegate fans out one item
    Then the child lifecycle parameterization is "remote-async"
    And the child lifecycle state is "working"

  # Spec 344 — lifecycle transition events (the event bus). move emits:
  # terminal/blocked → durable graph Event; churn → monitor channel only.

  Scenario: intermediate churn goes to the monitor, not the graph
    Given an opened lifecycle
    When I move the lifecycle to "working"
    Then no lifecycle_transition Event exists in the graph
    And a lifecycle transition MonitorEvent was emitted

  Scenario: a terminal transition is durable graph provenance
    Given an opened lifecycle
    When I move the lifecycle to "working"
    And I move the lifecycle to "completed"
    Then a lifecycle_transition Event to "completed" exists in the graph
    And that Event is OBSERVED_DURING the intent and the lifecycle
    And a lifecycle transition MonitorEvent was emitted

  Scenario: a blocked transition is durable graph provenance
    Given an opened lifecycle
    When I move the lifecycle to "input-required"
    Then a lifecycle_transition Event to "input-required" exists in the graph

  Scenario: a gate pause emits a durable transition event for free
    Given an opened lifecycle
    When a gate fails on the lifecycle
    Then a lifecycle_transition Event to "input-required" exists in the graph

  Scenario: the durable transition trail is recoverable without polling
    Given an opened lifecycle
    When I move the lifecycle to "working"
    And I move the lifecycle to "completed"
    Then the durable transition trail has 1 events

  Scenario: transitions appear in the intent timeline
    Given an opened lifecycle
    When I move the lifecycle to "completed"
    Then a lifecycle_transition event appears in manage.timeline for the intent
