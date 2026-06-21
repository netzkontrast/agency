Feature: Agent as a Lifecycle parameterization — Spec 342
  An agent IS a Lifecycle parameterization: a named machine variant whose
  transitions insert an observer (verify / in-review) so COMPLETED != done.
  One reducer — ctx.lifecycle.advance — runs the declared observer BY NAME
  (registry data, never a hardcoded caller) and maps its verdict to a move.
  Every driver caller calls the SAME advance.

  Background:
    Given a fresh agency engine for parameterization
    And a confirmed parameterization intent

  Scenario: a remote-async lifecycle cannot complete without verify
    Given a lifecycle opened with parameterization "remote-async" moved to "working"
    When I move the parameterized lifecycle directly to "completed"
    Then the parameterized move raises IllegalTransition
    And moving it through "verify" then "completed" succeeds

  Scenario: a default lifecycle completes directly
    Given a lifecycle opened with parameterization "default" moved to "working"
    When I move the parameterized lifecycle directly to "completed"
    Then the parameterized move succeeds

  Scenario: a parameterization declares its observer by name (registry data)
    Then the "remote-async" machine declares observer capability "jules" verb "verify"
    And the "reviewed" machine declares observer capability "gate" verb "check"

  Scenario: jules declares the remote-async parameterization
    Then the jules capability declares parameterization "remote-async"

  Scenario: fan_out opens a jules child with the remote-async parameterization
    When I fan out 1 jules-driven item
    Then the fanned child lifecycle has machine "remote-async"

  Scenario: advance runs the observer and completes when the branch is on origin
    Given a remote-async child in "verify" with branch "feat/x" present on origin
    When I advance the child
    Then the child moves to "completed"
    And advance reports done true

  Scenario: advance moves verify to input-required when the branch is missing
    Given a remote-async child in "verify" with branch "feat/x" absent from origin
    When I advance the child
    Then the child moves to "input-required"
    And advance reports done false

  Scenario: a verify lookup failure stays in verify, not failed
    Given a remote-async child in "verify" whose remote check errors
    When I advance the child
    Then the child stays in "verify"
    And advance reports done false

  Scenario: advance is a no-op for a default lifecycle with no observer
    Given a lifecycle opened with parameterization "default" moved to "working"
    When I advance the child
    Then advance reports no observer ran

  Scenario: advance is the ONE path — a new parameterization needs no caller edit
    Given a registered parameterization "audited" whose observer is "jules.verify"
    And a child opened with parameterization "audited" in "verify" with branch present
    When I advance the child
    Then the child moves to "completed"
    And advance reports done true

  Scenario: delegate.join runs advance so join's done equals the observer's done
    Given a remote-async child fanned out and driver-reported into "verify" with branch absent
    When delegate.join reduces the delegation
    Then join reports done false
    And the joined child is in "input-required"
