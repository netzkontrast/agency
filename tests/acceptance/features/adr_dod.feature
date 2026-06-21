Feature: ADR Definition-of-Done gate (Spec 355 Slice 1)

  Ports SPEC-001-E as a decidable pre-approval gate: `adr.dod_check` runs the
  automated criteria (reusing 354 `validate` — no duplicated rule logic) and
  `adr.approve` is the hinge — it blocks on a failed automated criterion, pauses
  at the human criteria (Evidence/Agreement) via `ctx.elicit`, records a `Gate`
  node either way, and only the intent OWNER (never the agent) may confirm or
  override. On confirmation the decision advances to `approved`.

  Background:
    Given a fresh agency engine in code-mode
    And a confirmed intent

  Scenario: dod_check passes the automated criteria for a well-formed decision
    Given a well-formed decision under a theme
    When I run the DoD check
    Then the DoD auto checks pass
    And the DoD check lists at least one human-pending criterion

  Scenario: approve blocks when an automated criterion fails
    Given a decision with only one neglected alternative
    When I approve it as "owner-alice"
    Then the decision is not approved
    And the decision status remains "proposed"

  Scenario: approve confirms a well-formed decision by the owner
    Given a well-formed decision under a theme
    When I approve it as "owner-alice"
    Then the decision is approved
    And the decision status is "approved"

  Scenario: an owner override approves a decision that fails the automated gate
    Given a decision with only one neglected alternative
    When I override-approve it as "owner-alice"
    Then the decision is approved
    And the approval records an override

  Scenario: an agent may not self-approve via override
    Given a decision with only one neglected alternative
    When I override-approve it as "agent"
    Then the decision is not approved

  Scenario: approve pauses for human confirmation when no approver is present
    Given a well-formed decision under a theme
    When I approve it with no approver
    Then the approval is input-required
    And the decision status remains "proposed"

  # ── Slice 2 — decision-status governed by the `decision` machine ─────────────

  Scenario: an illegal decision-status transition is rejected (DEC-001)
    Given a well-formed decision under a theme
    When I update the decision status to "retired"
    Then the status update is rejected with rule "DEC-001"
    And the decision status remains "proposed"

  Scenario: a cadence-lapsed approved decision is swept to expired
    Given a well-formed decision under a theme
    When I override-approve it as "owner-alice"
    And I set the decision next_review to "2000-01-01"
    And I run the review sweep
    Then the decision status is "expired"
