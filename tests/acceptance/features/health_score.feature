Feature: Health Score — computed, preset-weighted (Spec 381)

  The Health Score is a pure function over the recorded findings:
  score = max(0, 100 - Σ deduction(tier, preset)). The per-tier deductions are a
  documented tunable budget (strict/balanced/legacy-friendly), never a pinned
  score. "Leverage" is a defined computed quantity — deduction_weight × occurrence
  — so the report can name the highest-impact fixes.

  Background:
    Given an engine and confirmed intent

  Scenario: the score is computed per preset, not pinned
    Given findings of 1 critical, 2 warning, and 3 suggestion
    When I score them under "balanced"
    Then the health score is 72
    And the same findings score strictly lower under "strict"
    And the same findings score strictly higher under "legacy-friendly"

  Scenario: the score never drops below zero
    Given findings of 10 critical
    When I score them under "balanced"
    Then the health score is 0

  Scenario: an unknown preset falls back to balanced
    Given findings of 1 critical, 2 warning, and 3 suggestion
    When I score them under "nonsense"
    Then the health score is 72

  Scenario: leverage ranks the highest-impact fix first
    Given a recurring "R1" warning four times and a one-off "R2" critical
    When I rank fixes by leverage under "balanced"
    Then the top-leverage fix has risk_code "R1"
