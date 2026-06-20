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
    When I move the lifecycle to "working"
    And I move the lifecycle to "input-required"
    Then a lifecycle_transition Event to "input-required" exists in the graph

  Scenario: a gate pause emits a durable transition event for free
    Given an opened lifecycle
    When I move the lifecycle to "working"
    And a gate fails on the lifecycle
    Then a lifecycle_transition Event to "input-required" exists in the graph

  Scenario: the durable transition trail is recoverable without polling
    Given an opened lifecycle
    When I move the lifecycle to "working"
    And I move the lifecycle to "completed"
    Then the durable transition trail has 1 events

  Scenario: transitions appear in the intent timeline
    Given an opened lifecycle
    When I move the lifecycle to "working"
    And I move the lifecycle to "completed"
    Then a lifecycle_transition event appears in manage.timeline for the intent

  # Spec 340 — the enforced A2A transition table (the state machine).

  Scenario: a legal transition succeeds
    Given an opened lifecycle
    When I move the lifecycle to "working"
    Then the opened lifecycle state is "working"

  Scenario: an illegal transition from a terminal state raises
    Given an opened lifecycle
    When I move the lifecycle to "working"
    And I move the lifecycle to "completed"
    And I move the lifecycle to "working" expecting an illegal transition
    Then the move is rejected as an illegal transition with allowed "[]"

  Scenario: a skip transition raises
    Given an opened lifecycle
    When I move the lifecycle to "completed" expecting an illegal transition
    Then the move is rejected as an illegal transition

  Scenario: the seed table is internally consistent
    Then every state in the transition table is a valid lifecycle state

  Scenario: a graph override is read instead of the seed and stays floor-safe
    Given a transition-table override adding "submitted" to "completed"
    When I move an opened lifecycle to "completed"
    Then the opened lifecycle state is "completed"

  Scenario: an override cannot reopen a terminal state
    Given a transition-table override adding "completed" to "working"
    Then loading the effective table is rejected

  # Spec 349b — lifecycle transitions fan onto the pillar event bus.

  Scenario: a transition fans onto the Spec 349 event bus
    Given a subscriber registered for the lifecycle transition event
    And an opened lifecycle
    When I move the lifecycle to "working"
    Then the subscriber received a transition to "working"

  # Spec 341 — observe suite: read · find · check · watch (the read frame).
  # read: full node + serving intent; find: query by intent/state;
  # check: boolean state test; watch: durable 344 trail, no poll.

  Scenario: read returns the full lifecycle node with its serving intent
    When I open a lifecycle serving the intent
    Then lifecycle.read returns the state "submitted"
    And lifecycle.read includes the serving intent_id

  Scenario: find returns all lifecycles serving an intent
    When I open a lifecycle serving the intent
    Then lifecycle.find for the intent returns 1 lifecycle

  Scenario: find filtered by state returns only matching lifecycles
    Given an opened lifecycle
    When I move the lifecycle to "working"
    Then lifecycle.find for the intent in state "working" returns 1 lifecycle
    And lifecycle.find for the intent in state "submitted" returns 0 lifecycles

  Scenario: check returns True when lifecycle is in the given state
    Given an opened lifecycle
    Then lifecycle.check for "submitted" is true
    And lifecycle.check for "working" is false

  Scenario: watch returns the durable transition trail without polling
    Given an opened lifecycle
    When I move the lifecycle to "working"
    And I move the lifecycle to "completed"
    Then lifecycle.watch returns 1 transition event
    And the first watch event is a transition to "completed"

  Scenario: watch returns no events for churn-only transitions
    Given an opened lifecycle
    When I move the lifecycle to "working"
    Then lifecycle.watch returns 0 transition events

  Scenario: the lifecycle_read substrate tool returns the full node
    Given an opened lifecycle via the lifecycle_open substrate tool
    Then the lifecycle_read substrate tool returns state "submitted"

  Scenario: the lifecycle_find substrate tool returns lifecycles for an intent
    When I open a lifecycle serving the intent
    Then the lifecycle_find substrate tool returns 1 lifecycle for the intent

  Scenario: the lifecycle_watch substrate tool returns the transition trail
    Given an opened lifecycle via the lifecycle_open substrate tool
    When I move the lifecycle to "working"
    And I close the lifecycle as "completed"
    Then the lifecycle_watch substrate tool returns 1 transition event

  Scenario: the lifecycle_check substrate tool returns match true for the current state
    Given an opened lifecycle via the lifecycle_open substrate tool
    Then the lifecycle_check substrate tool matches "submitted"
    And the lifecycle_check substrate tool does not match "working"

  Scenario: find returns all lifecycles when an intent has multiple
    When I open two lifecycles serving the intent
    Then lifecycle.find for the intent returns 2 lifecycles
