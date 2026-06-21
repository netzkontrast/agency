Feature: SARIF emit from structured findings (Spec 382 §1)

  Findings are born structured (Spec 360 Finding nodes), so SARIF 2.1.0 renders
  straight from them — no report-parse step. The rule set is DERIVED from the live
  decay-risk registry (never a pinned list), levels map from the tier, and the
  emit is capped with a truncation locator (never a silent drop).

  Background:
    Given an engine and confirmed intent

  Scenario: SARIF renders from structured findings without parsing
    Given findings including an R5 critical with consequence and remedy
    When I render SARIF
    Then the SARIF version is "2.1.0"
    And the R5 result level is "error"
    And the R5 result message carries the consequence and the remedy

  Scenario: the SARIF rule set is derived from the live registry, not pinned
    Given no findings
    When I render SARIF
    Then the SARIF rule ids equal the live decay-risk registry

  Scenario: SARIF is capped with a truncation locator, never silently dropped
    Given 10 findings
    When I render SARIF with max_results 3
    Then at most 3 results are emitted
    And the SARIF reports "3 of 10 shown"
