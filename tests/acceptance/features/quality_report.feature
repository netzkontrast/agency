Feature: Iron-Law report render (Spec 382 §4)

  The human-readable report projects the structured findings: a header with the
  Health Score, findings sorted by tier (critical→warning→suggestion) each as the
  Iron Law block (Symptom / Source / Consequence / Remedy), empty tiers omitted,
  and a mermaid Module Dependency Graph in audit mode only. (The template FILE is
  authored in Spec 384; this slice owns the render path.)

  Background:
    Given an engine and confirmed intent

  Scenario: the report renders the Iron Law, sorted by tier
    Given findings of one R5 critical and one R1 warning
    When I render the report for mode "review" with score 80
    Then the report header shows score 80
    And the critical finding appears before the warning finding
    And the report shows Symptom, Source, Consequence, and Remedy for the R5 finding
    And the suggestion tier is omitted

  Scenario: audit mode includes a mermaid Module Dependency Graph
    Given findings of one R5 critical and one R1 warning
    When I render the report for mode "audit" with score 80
    Then the report contains a mermaid block

  Scenario: review mode omits the mermaid graph
    Given findings of one R5 critical and one R1 warning
    When I render the report for mode "review" with score 80
    Then the report contains no mermaid block
