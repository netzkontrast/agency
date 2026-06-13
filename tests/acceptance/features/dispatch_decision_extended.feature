Feature: Delegate dispatch_decision — extended signals S1, S6, S7, S8 (Spec 040)
  The seven signals added after the original four (S2–S5 covered in delegate.feature)
  complete the eleven-signal heuristic. Observable behaviour: the recommendation,
  driver, signals_fired, token_cost_estimate, and local_budget_token_estimate keys
  in the payload. Two disqualifiers (S6, S10-override) run BEFORE positive scoring.

  Background:
    Given a fresh agency engine in code-mode
    And a confirmed intent

  # ── payload shape ──────────────────────────────────────────────────────────

  Scenario: payload carries all six required keys
    When I call dispatch_decision with no arguments
    Then the payload has recommendation driver rationale token_cost_estimate local_budget_token_estimate and signals_fired

  Scenario: inline recommendation has driver inline and empty signals
    When I call dispatch_decision with no arguments
    Then the dispatch recommendation is "inline"
    And the selected driver is "inline"
    And no signals are fired
    And local_budget_token_estimate equals token_cost_estimate

  # ── S1 — expected_return_tokens ─────────────────────────────────────────────

  Scenario: S1 high return tokens fires and dispatches
    When I call dispatch_decision with expected_return_tokens 8000
    Then the dispatch recommendation is "dispatch"
    And the signals include one starting with "S1"

  Scenario: S1 low return tokens does not swing inline
    When I call dispatch_decision with expected_return_tokens 2000
    Then the dispatch recommendation is "inline"

  # ── S6 — mutates (disqualifier) ─────────────────────────────────────────────

  Scenario: S6 mutates disqualifies dispatch even when other signals fire
    When I call dispatch_decision with mutates true and file_count 6 and return_tokens 8000
    Then the dispatch recommendation is "inline"
    And the signals include one starting with "S6"

  # ── S7 — read_only amplifies ────────────────────────────────────────────────

  Scenario: S7 read_only amplifies when another signal fires
    When I call dispatch_decision with read_only true and file_count 4
    Then the dispatch recommendation is "dispatch"
    And the signals include one starting with "S7"

  Scenario: S7 alone does not swing the decision
    When I call dispatch_decision with read_only true and no other signals
    Then the dispatch recommendation is "inline"

  # ── S8 — driver_hint ────────────────────────────────────────────────────────

  Scenario: S8 driver_hint jules selects jules when not conflicting
    When I call dispatch_decision with driver_hint jules and file_count 4
    Then the selected driver is "jules"
    And the signals include one starting with "S8"

  Scenario: S8 driver_hint local selects local driver
    When I call dispatch_decision with driver_hint local and file_count 4
    Then the selected driver is "local"
    And the signals include one starting with "S8"
