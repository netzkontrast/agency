Feature: triage — suppression + acknowledgement (Spec 381 §4)

  Triage is an intent judgment about a finding: dismiss records a Suppression,
  accept records an Acknowledgement (both on the intent ontology), and the
  SUPPRESSES edge crosses to the analyze Finding. The scan-time scoring read is an
  analyze concern: a finding matching a live Suppression is excluded from the
  score; an expired suppression lets the finding resurface (keep-both — the
  finding node is never deleted).

  Background:
    Given an engine and confirmed intent

  Scenario: dismissing a finding records a Suppression with provenance
    Given a recorded R3 finding in "src/util.py"
    When I triage it with action "dismiss" and reason "false positive in generated glue"
    Then a Suppression records risk "R3", pattern "src/util.py", and the reason
    And the Suppression SUPPRESSES the finding
    And the finding node still exists

  Scenario: accepting a finding records an Acknowledgement
    Given a recorded R3 finding in "src/util.py"
    When I triage it with action "accept" and reason "known, accepted debt"
    Then an Acknowledgement records risk "R3" and the reason

  Scenario: a dismissed risk is excluded from the next score
    Given a live Suppression for risk "R3" pattern "src/util.py"
    When I score findings of an R3 in "src/util.py" and an R1 in "app.py"
    Then 1 finding is suppressed at scan time
    And only 1 finding is scored

  Scenario: an expired suppression lets the finding resurface
    Given an expired Suppression for risk "R3" pattern "src/util.py"
    When I score findings of an R3 in "src/util.py"
    Then 1 finding is scored
    And 1 suppression is reported expired
