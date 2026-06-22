Feature: loop detection — middleware and typed LoopEvent (Spec 011 / 156)
  The loop-detection layer catches repeated identical tool invocations and
  near-duplicate message/result streams. It is pure middleware — not a
  discoverable verb — and returns a structured result with a confidence score.

  Scenario: identical repeated tool results trigger loop detection at confidence 1.0
    When I run loop detection on a window with three identical tool results
    Then detected is True
    And confidence is 1.0
    And the evidence indices span two of the duplicate positions

  Scenario: distinct inputs do not trigger loop detection
    When I run loop detection on a window with diverse messages and results
    Then detected is False
    And confidence is below 0.7

  Scenario: empty inputs are safe and return not-detected
    When I run loop detection on empty messages and results
    Then the result is detected False confidence 0.0 evidence None

  Scenario: two identical messages cross the threshold
    When I run loop detection with two identical messages
    Then detected is True and confidence is 1.0

  Scenario: loop detector is not exposed as a discoverable verb
    Given a fresh agency engine in code-mode
    When I list all registered capability verbs
    Then detect_loop is not among them
    And detect_loops is not among them

  Scenario: LoopEvent requires at least one evidence id
    When I create a LoopEvent with an empty evidence tuple
    Then a ValueError is raised

  Scenario: LoopEvent rejects an invalid kind
    When I create a LoopEvent with kind bogus
    Then a ValueError is raised

  Scenario: detect_loops flags three identical commits in a window
    When I call detect_loops on a stream with three identical git commit events
    Then at least one LoopEvent is returned with kind loop_detected
    And the evidence ids are a subset of the three identical events

  Scenario: detect_loops returns empty for a diverse event stream
    When I call detect_loops on a stream of five distinct git commit events
    Then no LoopEvents are returned

  Scenario: detect_loops respects window size
    When I call detect_loops with window 2 on a stream where duplicates are beyond the window
    Then no LoopEvents are returned

  Scenario: two identical events do not constitute a loop but three do
    When I call detect_loops on exactly two identical events
    Then no LoopEvents are returned
    When I call detect_loops on exactly three identical events
    Then a LoopEvent is returned

  Scenario: detect_loops preserves evidence order oldest first
    When I call detect_loops on an ordered stream with three identical events after a different one
    Then the evidence tuple lists the three duplicate event ids in order
