Feature: The loop-design wizard — Spec 367 (a walkable skill on the spine)
  Looper's 7-stage interview is a walkable skill registered into the develop
  ontology (no new capability). It delivers one phase at a time; the council and
  control phases are hard gates (the two invariants looper refuses to emit
  without); phase 6 shows a graph-derived ASCII preview before sign-off.

  Background:
    Given a fresh agency engine in code-mode

  Scenario: the wizard is registered and walks one phase at a time
    Then the engine ontology exposes the "loop-design" skill
    When I start walking the loop-design skill
    Then the walker offers phase 1 "goal" only
    And advancing offers phase 2 "verification"

  Scenario: the council and control phases are hard gates
    Then the loop-design "council" phase is a hard gate
    And the loop-design "control" phase is a hard gate

  Scenario: the reviewer-only rule decides the council gate
    Given an open loop with only a reviewer member
    Then a verdict source is not present for the loop
    When I add a judge member to the loop
    Then a verdict source is present for the loop

  Scenario: a termination guard decides the control gate
    Then a control with no caps has no termination guard
    And a control with max_iterations has a termination guard

  Scenario: the confirm phase shows a graph-derived preview
    Given an open loop with a programmatic criterion and a judge member
    When I render the loop preview
    Then the preview shows the loop flow, the criteria, the council, and the stops

  Scenario: walking the wizard records a SkillRun that serves the intent
    When I walk the loop-design skill to completion
    Then a Skill named "loop-design" serves the intent with seven phase records
