Feature: discover.interview — the adaptive elicitation engine (Spec 309)
  Turns a one-sentence seed into a DRAFT Intent via an adaptive beat-chain, where
  each beat's question is derived from the prior answer, and every turn is a graph
  node the discovery can replay (Goal 2). Generalizes Spec 262's fixed four.

  Background:
    Given a fresh agency engine in code-mode
    And a confirmed intent

  Scenario: every beat is recorded as a turn the session elicited
    When I interview "build a CLI" with answers "ship a fast CLI|a binary|tests pass" and max 6 beats
    Then the session elicits as many turns as beats reported
    And every turn carries a non-empty verbatim answer

  Scenario: the next beat's question adapts to the prior answer
    When I interview "build a CLI" with answers "ship a fast CLI|a binary|tests pass" and max 6 beats
    Then the second beat question embeds the first beat answer

  Scenario: the interview produces a draft Intent the session discovered
    When I interview "build a CLI" with answers "ship a fast CLI|a binary|tests pass" and max 6 beats
    Then the produced intent has status draft
    And the session discovered the produced intent

  Scenario: a sharp interview completes before the budget
    When I interview "build a CLI" with answers "ship a fast CLI|a binary|tests pass" and max 6 beats
    Then the interview terminates complete with fewer turns than the budget

  Scenario: a vague interview runs to the budget
    When I interview "vague" with answers "only one|two" and max 2 beats
    Then the interview terminates by max_beats with exactly 2 turns

  Scenario: the Driver seam is optional — a stub NextBeat records the same surface
    Given a stub next-beat driver is injected
    When I interview "build a CLI" with answers "ship a fast CLI|a binary|tests pass" and max 6 beats
    Then the session elicits as many turns as beats reported
    And the session discovered the produced intent
