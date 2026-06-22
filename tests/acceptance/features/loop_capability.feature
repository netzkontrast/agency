Feature: The loop capability — Spec 387 W1 (reachable + records provenance)
  The looper port's verbs are a discoverable, schema'd, executable capability —
  not invisible module functions. Every loop verb is on the wire surface and,
  invoked, records an Invocation serving the intent (the provenance moat the bare
  spine functions 363-369 bypassed). This is the dormant-surface audit as a
  standing test: it would have FAILED on the spine-only port.

  Background:
    Given a fresh agency engine in code-mode
    And a confirmed intent

  Scenario: the loop verbs are on the wire surface (reachability)
    Then the wire surface exposes the loop verbs frame_goal, open, advance, compile, emit
    And get_schema returns a schema for the loop open verb

  Scenario: invoking a loop verb records an Invocation serving the intent (the moat)
    When I invoke the loop frame_goal verb through the registry
    Then an Invocation with capability loop serves the intent
    And the goal is framed as an Intent

  Scenario: the loop capability is discoverable by query
    When I search the live registry for "design an agent loop"
    Then a loop verb is among the results
