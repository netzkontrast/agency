Feature: Delegate capability — dispatch decision and fan-out/join
  delegate weighs the eleven-signal heuristic before dispatching, fans tasks
  out to child lifecycles (recording DELEGATES_TO edges), and reduces results
  back via join (Spec 040/041).

  Background:
    Given a fresh agency engine in code-mode
    And a confirmed intent

  # ── dispatch_decision ────────────────────────────────────────────────────

  Scenario: dispatch_decision recommends inline when no signals fire
    When I call dispatch_decision with file_count 1 parallelism 1 and duration 3
    Then the dispatch recommendation is "inline"
    And no signals are fired
    And the rationale is non-empty

  Scenario: dispatch_decision recommends dispatch on high file count
    When I call dispatch_decision with file_count 4
    Then the dispatch recommendation is "dispatch"
    And the signals include one starting with "S2:files"

  Scenario: dispatch_decision recommends dispatch on exploration needed
    When I call dispatch_decision with exploration_needed true
    Then the dispatch recommendation is "dispatch"
    And the signals include one starting with "S3:explore"

  Scenario: dispatch_decision recommends dispatch on high parallelism
    When I call dispatch_decision with parallelism 3
    Then the dispatch recommendation is "dispatch"
    And the signals include one starting with "S4:parallel"

  Scenario: dispatch_decision recommends dispatch on long duration
    When I call dispatch_decision with est_duration_min 15
    Then the dispatch recommendation is "dispatch"
    And the signals include one starting with "S5:duration"

  Scenario: S9 high overlap with low return keeps task inline
    When I call dispatch_decision with file_count 6 context_overlap 0.8 and return_tokens 2000
    Then the dispatch recommendation is "inline"
    And the signals include one containing "S9"

  Scenario: S10 hot cache with short duration keeps task inline
    When I call dispatch_decision with file_count 5 cache_warmth 0.8 and duration 5
    Then the dispatch recommendation is "inline"
    And the signals include one containing "S10"

  Scenario: S11 routes to Jules despite low return tokens
    When I call dispatch_decision with local_budget_relevant false and return_tokens 2500
    Then the dispatch recommendation is "dispatch"
    And the selected driver is "jules"
    And the local_budget_token_estimate equals 0

  Scenario: Jules dispatch has zero local budget cost
    When I call dispatch_decision with local_budget_relevant false and duration 60
    Then the selected driver is "jules"
    And the local_budget_token_estimate equals 0
    And the total_token_cost_estimate is positive

  Scenario: local dispatch has non-zero local budget
    When I call dispatch_decision with file_count 5 and parallelism 3
    Then the selected driver is "local"
    And the local_budget_token_estimate is positive

  # ── dispatch_bash_hints ──────────────────────────────────────────────────

  Scenario: dispatch_bash_hints is empty when no args given
    When I call dispatch_bash_hints with no args
    Then the hints list is empty
    And the hints block is empty

  Scenario: dispatch_bash_hints renders find per path
    When I call dispatch_bash_hints with paths "agency/capabilities,tests"
    Then each path appears in a find hint
    And the block contains a bash code fence

  Scenario: dispatch_bash_hints renders grep per symbol
    When I call dispatch_bash_hints with symbols "lint_prompt,review_comment"
    Then each symbol appears in a grep hint

  Scenario: dispatch_bash_hints is injection-safe for shell metacharacters
    When I call dispatch_bash_hints with a symbol containing shell metacharacters
    Then the metacharacter sequence cannot break out of the argument

  # ── fan_out + join ────────────────────────────────────────────────────────

  Scenario: fan_out opens one child lifecycle per item and records DELEGATES_TO
    When I fan out 2 items to the reflect capability
    Then a Delegation node is recorded with count 2
    And the Delegation SERVES the intent
    And each child lifecycle has a DELEGATES_TO edge from the Delegation

  Scenario: fan_out respects the quota cap
    When I fan out 5 items with quota 3
    Then only 3 children are dispatched
    And 2 items are skipped

  Scenario: fan_out rejects a negative quota
    When I fan out items with quota -1
    Then the negative-quota fan_out carries an error

  Scenario: fan_out rejects non-mapping items
    When I fan out a list containing a non-mapping item
    Then the nonmap fan_out carries an error

  Scenario: join reports done when all children are completed
    When I fan out 1 item and mark the child completed
    Then the join over a completed child reports done true

  Scenario: join reports done false when children are still working
    When I fan out 1 item without completing the child
    Then the join over working children reports done false
    And the join working-child count in "working" state is 1

  Scenario: join rejects a delegation from a different intent
    When I join a delegation that serves a different intent
    Then the cross-intent join carries an error
