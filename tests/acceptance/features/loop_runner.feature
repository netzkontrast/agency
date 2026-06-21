Feature: Loop external runner, model detection & egress — Spec 369
  The loop's out-of-session twin: model detection over the allowlist (metadata
  only, no secrets), the ported stdlib run-loop.py reading only the resolved
  spec, and one narrow egress-consent gate (cross-vendor consent + redaction)
  for both surfaces. Carries the 362 closers: the provenance moat + parity.

  Background:
    Given a fresh agency engine in code-mode

  Scenario: detect_models records invocation metadata only, never secrets
    When I detect models with claude and ollama installed
    Then the available models list their argv invocations, families, and local flags
    And no secret-shaped material appears anywhere in the result

  Scenario: register_model rejects a non-argv or secret-shaped invocation
    Then register_model with a shell-string invoke is rejected
    And register_model with a key in the argv is rejected
    And register_model with a clean argv is accepted

  Scenario: the emitted runner reads only the resolved spec and imports only stdlib
    When I emit the runner
    Then run-loop.py loads loop.resolved.json and imports only the Python stdlib

  Scenario: a local member sends with no consent prompt
    Then a local member requires no egress consent

  Scenario: a cross-vendor send requires first-send consent recorded as provenance
    Given an open loop served by a goal
    When a cross-vendor judge needs consent and the user grants it
    Then the first send is blocked for consent and the granted consent is a graph node

  Scenario: redaction globs apply before any send
    Then a secrets path is redacted before a cross-vendor send

  Scenario: in-session and external runs honor the same termination contract
    Given an open loop served by a goal
    Then control_evaluate is deterministic and the emitted runner reads the same control fields

  Scenario: the provenance moat is lit end-to-end
    When I run the full loop pipeline to completion
    Then the whole chain is recoverable from the graph
