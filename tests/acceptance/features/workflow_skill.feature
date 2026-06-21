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

  # ── Slice 2 — the ADR-hinge step verbs (end-to-end dogfood) ───────────────────

  Scenario: the hinge step verbs carry a spec from open to inprogress with hints
    Given an ingested spec with decisions
    When I open the spec to extract its decisions
    And I attempt to begin implementation
    Then implementation is blocked on unapproved decisions
    When I approve the spec decisions as owner "owner-alice"
    And I attempt to begin implementation
    Then implementation begins with hints loaded

  Scenario: the owner marks the spec done (the done-cascade)
    Given an ingested spec with decisions
    When I open the spec to extract its decisions
    And I approve the spec decisions as owner "owner-alice"
    And I attempt to begin implementation
    And I mark the spec done as owner "owner-alice"
    Then the spec is recorded done
