Feature: discover.scope — in/out-of-scope boundary elicitation (Spec 318)
  Draws candidate boundaries from the Intent's grounding (GROUNDS citations),
  composes discover.ask (310) for the well-formed question, and records each
  decided boundary as a ScopeBoundary BOUNDS-edged to the Intent — fencing the
  deliverable against creep. The undecided ones stay open (no node).

  Background:
    Given a fresh agency engine in code-mode
    And a confirmed intent

  Scenario: candidates derive from grounding and the question is well-formed
    When I scope a grounded intent
    Then every scope candidate derives from a grounding citation
    And the scope question is a well-formed ask payload

  Scenario: decided boundaries bound the intent and the partition holds
    When I scope a grounded intent
    Then bounds edges equal the decided boundary count
    And in-scope out-of-scope and open partition the candidates
    And every boundary side is in or out

  Scenario: an undecided candidate stays open with no node
    When I scope a grounded intent
    Then the undecided candidate is open with no boundary node
