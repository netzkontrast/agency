Feature: the develop-spec repo-development workflow (Spec 358)

  `develop-spec` is the walkable through-line of the owner's process — intent →
  triage → brainstorm → research → acceptance → spec → spec-panel → Brooks-lint →
  improve-loop → the ADR hinge (open → extract → approve → inprogress) → build →
  done. The walker delivers ONE phase at a time and pauses at the HARD gates: the
  design improve-gate and the ADR-approval hinge (a spec cannot reach inprogress
  until its decisions are approved — 355/356).

  Background:
    Given a fresh agency engine in code-mode
    And a confirmed intent

  Scenario: develop-spec is registered and walkable
    When I start the develop-spec walk
    Then the first phase is "intent"

  Scenario: the walk pauses at the design improve-gate
    When I walk develop-spec with the design inputs
    Then the walk pauses at the "improve" hard gate
    And the walked phases are recorded as provenance

  Scenario: confirming the improve-gate advances to the ADR-approval hinge
    When I walk develop-spec with the design inputs
    And I resume the walk past the improve gate
    Then the walk pauses at the "adr-approve" hard gate
