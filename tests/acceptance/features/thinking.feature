Feature: thinking capability — critical-thinking method scaffolds (Spec 110)
  The thinking capability returns structured reasoning scaffolds (decompose,
  assumptions, premortem, red_team, …) the agent fills out, and a composite
  full-review that sequences the founding methods into a thinking-analysis.

  Background:
    Given a fresh agency engine in code-mode
    And a confirmed intent

  Scenario: a method scaffold defaults its subject to the serving intent
    When I run thinking.decompose with no subject
    Then the scaffold method is "decompose"
    And the scaffold subject is non-empty
    And the scaffold lists reasoning steps

  Scenario: a method uses an explicit subject when given
    When I run thinking.assumptions for "the caching layer"
    Then the scaffold subject is "the caching layer"

  Scenario: the net-new red_team method returns a scaffold for its subject
    When I run thinking.red_team for "the rollout plan"
    Then the scaffold method is "red_team"
    And the scaffold subject is "the rollout plan"

  Scenario: apply_full_review sequences the eight founding methods into an analysis
    When I run thinking.apply_full_review
    Then the analysis covers eight founding methods
    And every covered method carries a scaffold

  Scenario: apply_full_review rejects an unknown depth
    When I run thinking.apply_full_review with depth "nope"
    Then no analysis is produced
