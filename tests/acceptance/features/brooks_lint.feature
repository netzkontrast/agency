Feature: Brooks-lint — conceptual-integrity critical-thinking pass (Spec 359)

  `intent.brooks_lint` is the 9th critical-thinking method: a decidable,
  evidence-anchored conceptual-integrity pass (Fred Brooks) over a spec/design.
  It advises — `block` is reserved for conceptual-integrity / irreversible-surface
  violations; everything else is warn/info. Works with no API key.

  Background:
    Given a fresh agency engine in code-mode
    And a confirmed intent

  Scenario: a coherent spec passes the conceptual-integrity check
    When I brooks-lint a coherent spec
    Then the spec is conceptually coherent

  Scenario: a spec that introduces a parallel store is blocked
    When I brooks-lint a spec that adds a parallel store
    Then a brooks finding has principle "conceptual-integrity" with severity "block"
    And the spec is not conceptually coherent

  Scenario: a gold-plated spec is flagged as a second-system warning
    When I brooks-lint a gold-plated spec
    Then a brooks finding has principle "second-system" with severity "warn"

  Scenario: every brooks finding cites evidence
    When I brooks-lint a spec that adds a parallel store
    Then every brooks finding cites evidence
