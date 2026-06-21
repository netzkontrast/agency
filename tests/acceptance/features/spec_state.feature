Feature: spec-state lifecycle — specs as Lifecycles on the `spec` machine (Spec 357)

  A spec's state is a real Lifecycle (Spec 339/345 `spec` machine: draft → open →
  inprogress → done, + superseded), advanced ONLY via ctx.lifecycle.move. The
  open→inprogress transition is gated by the ADR hinge (adr.spec_decisions_ready):
  a spec cannot start implementation until its extracted decisions are approved.

  Background:
    Given a fresh agency engine in code-mode
    And a confirmed intent

  Scenario: open_spec mints a SpecLifecycle in draft tracking the spec
    Given an ingested spec document
    When I open the spec lifecycle
    Then the spec state is "draft"

  Scenario: a spec advances draft to open
    Given an ingested spec document
    When I open the spec lifecycle
    And I move the spec to "open"
    Then the spec state is "open"

  Scenario: an illegal spec transition is rejected
    Given an ingested spec document
    When I open the spec lifecycle
    And I move the spec to "done"
    Then the spec move is rejected

  Scenario: open to inprogress is blocked until the ADR decisions are approved
    Given an ingested spec document with two extracted decisions
    When I open the spec lifecycle
    And I move the spec to "open"
    And I move the spec to "inprogress"
    Then the spec move is blocked
    And the spec state is "open"
    When I approve every decision of the spec as owner "owner-alice"
    And I move the spec to "inprogress"
    Then the spec state is "inprogress"

  Scenario: any spec state can be superseded
    Given an ingested spec document
    When I open the spec lifecycle
    And I move the spec to "superseded"
    Then the spec state is "superseded"

  Scenario: superseding a spec records the forward reference to its replacement
    Given an ingested spec document
    When I open the spec lifecycle
    And I supersede the spec with a replacement
    Then the supersession records the replacement

  # ── the human surface: physical folders + the indexer ────────────────────────

  Scenario: index reports every spec with its state readings and flags drift
    Given a Plan tree with a clean, a drifted, and a legacy spec
    When I index the Plan tree
    Then the index flags the drifted spec
    And the index marks the legacy spec
    And the clean spec has no flags
