Feature: select capability — complexity-scored approach selection (Spec 296)
  Routes an operation to an approach archetype (semantic/pattern/native) by
  decidable complexity scoring, recorded as provenance.

  Background:
    Given a fresh agency engine in code-mode
    And a confirmed intent

  Scenario: the archetypes list the three approaches
    When I list the select archetypes
    Then the archetypes include semantic, pattern, and native

  Scenario: a symbol rename routes to semantic
    When I route the operation "rename a symbol across the project" over 10 files
    Then the selected approach is "semantic"
    And the selection records a Selection node serving the intent

  Scenario: a bulk pattern edit routes to pattern
    When I route the operation "bulk replace a pattern across all files with regex" over 8 files
    Then the selected approach is "pattern"

  Scenario: speed priority biases toward pattern
    When I route the speed-critical operation "replace text everywhere"
    Then the selected approach is "pattern"

  Scenario: memory operations are a direct mapping to semantic
    When I route the operation "save project context for cross-session memory"
    Then the selected approach is "semantic"
    And the selection rationale mentions a direct mapping

  Scenario: select exposes a walkable approach-routing discipline (Spec 301 superpowers pattern)
    When I walk the "approach-routing" discipline to its gate
    Then the discipline pauses at a hard gate
