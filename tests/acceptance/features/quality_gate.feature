Feature: the quality CI gate (Spec 382 §2/§3)

  The CI actor gates a PR on the Health Score + critical count: analyze.gate
  records an auditable Gate node (passed iff score >= min_score AND criticals <=
  max_critical); gate.verdict reads the latest Gate by name so CI exits non-zero
  on a block. Thresholds are documented tunable budgets (min_score 70, max_critical 0).

  Background:
    Given an engine and confirmed intent

  Scenario: the gate blocks below the score threshold, with provenance
    When I run the quality gate for mode "review" with score 60 and 0 criticals
    Then the gate is blocked
    And a Gate node "quality:review" records passed false with the score in its evidence

  Scenario: a critical over the max blocks even with a high score
    When I run the quality gate for mode "review" with score 95 and 1 criticals
    Then the gate is blocked

  Scenario: the gate passes above threshold with no criticals
    When I run the quality gate for mode "review" with score 85 and 0 criticals
    Then the gate passes

  Scenario: gate.verdict reads the latest gate as blocked
    Given a recorded quality gate for mode "review" with score 60 and 0 criticals
    When I read the gate verdict for "quality:review"
    Then the verdict is blocked

  Scenario: gate.verdict on an unknown gate is not blocked
    When I read the gate verdict for "quality:never-run"
    Then the verdict is not found and not blocked
