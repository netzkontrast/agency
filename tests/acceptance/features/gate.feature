Feature: Gate capability — record gate verdicts with provenance
  gate.check records a pass or block verdict on a Lifecycle node as auditable
  provenance; a failed gate pauses the lifecycle at input-required (Spec 011).

  Background:
    Given a fresh agency engine in code-mode
    And a confirmed intent

  Scenario: gate.check records a passing verdict
    Given an open lifecycle
    When I check gate "spec-validation" with passed true
    Then the gate result reports passed true
    And a Gate node named "spec-validation" is in the graph

  Scenario: gate.check records a blocking verdict and pauses the lifecycle
    Given an open lifecycle
    When I check gate "confidence" with passed false
    Then the direct gate result is blocked
    And the blocked lifecycle state is "input-required"

  Scenario: gate.check rejects a lifecycle that does not serve the current intent
    When I check gate "any" against a foreign lifecycle
    Then the gate result carries a lifecycle-guard error

  # ── predicates (via gate.check) ────────────────────────────────────────────

  Scenario: spec_validate passes a spec with normative keywords and a Gherkin scenario
    When I validate a spec with normative keywords and a Gherkin scenario
    Then the validation result is ok with no findings

  Scenario: spec_validate flags missing normative keywords
    When I validate a spec that has only a Gherkin scenario and no normative keywords
    Then the normative-keyword finding is flagged as "rfc2119"

  Scenario: spec_validate flags missing Gherkin
    When I validate a spec that has normative keywords but no Gherkin scenario
    Then the gherkin finding is flagged as "gherkin"

  Scenario: confidence_check passes when all claims are met
    When I confidence_check with all claims passing
    Then the confidence score is 1.0 and no claims are blocking

  Scenario: confidence_check blocks when fewer than threshold claims are met
    When I confidence_check with 2 of 5 claims passing
    Then the confidence score is 0.4 and 3 claims are blocking

  Scenario: sub-threshold confidence blocks the gate and pauses the lifecycle
    Given an open lifecycle
    When I run a sub-threshold confidence check through gate.check
    Then the sub-threshold gate result is blocked
    And the sub-threshold lifecycle state is "input-required"
