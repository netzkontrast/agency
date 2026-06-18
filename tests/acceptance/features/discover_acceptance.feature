Feature: discover.acceptance — Gherkin acceptance-criteria derivation (Spec 317)
  Derives testable, Gherkin-shaped criteria from the Intent's deliverable — each
  VALIDATES-edged to the Intent, each tagged measurable with the unmeasurable ones
  FLAGGED rather than accepted, plus a coverage note. The moat now holds checkable
  "done" conditions, not a wish.

  Background:
    Given a fresh agency engine in code-mode
    And a confirmed intent

  Scenario: criteria derive from deliverable sub-parts and each validates the intent
    When I derive acceptance for a deliverable "a fast binary and it works well and exits zero"
    Then every criterion derives from a deliverable sub-part
    And each criterion validates the intent exactly once
    And every criterion gherkin has Given When and Then clauses

  Scenario: an unmeasurable part is flagged, not dropped
    When I derive acceptance for a deliverable "a fast binary and it works well and exits zero"
    Then at least one criterion is flagged unmeasurable
    And the flagged criterion is still present

  Scenario: coverage partitions the deliverable parts
    When I derive acceptance for a deliverable "a fast binary and it works well and exits zero"
    Then covered plus gaps equals the deliverable part count
