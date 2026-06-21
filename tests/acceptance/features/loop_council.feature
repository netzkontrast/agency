Feature: The loop council — Spec 365 (cross-model review; reuse persona + panel)
  A council member is a reviewer (notes) or a judge (a gating verdict) bound to a
  model family. The reviewer-only rule keeps a revise_until_clean gate from
  declaring a delivery "clean" without a verdict source. Cross-model review (a
  member from a different family than the host) is the coaching default.

  Background:
    Given a fresh agency engine in code-mode
    And an open loop

  Scenario: a judge member on a different family is recorded and noted cross-family
    When I add a judge member on the "codex" family while the host is "claude"
    Then a member with role "judge" and family "codex" is recorded with a driver
    And recommend_council notes the member is cross-family

  Scenario: a judge revise verdict is structured and gates progression
    When the judge returns a revise verdict with blocking issues
    Then the verdict parses as "revise" and does not pass

  Scenario: an unparseable judge verdict degrades to revise and warns
    When the judge returns non-JSON council text
    Then the verdict is "revise" tagged "unparseable_judge_output"

  Scenario: the reviewer-only rule flags a revise_until_clean gate with no verdict source
    Given the council has only a reviewer member
    When I recommend_council
    Then verdict_sources_ok is false and a gate is listed as missing a verdict source
