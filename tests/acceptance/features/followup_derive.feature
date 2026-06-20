Feature: Per-spec Followup status — derived metrics (Spec 269)
  The Followup section's COMPUTED metrics (test count, Done-When checkbox
  ratio, recent commits, status) DERIVE from source instead of being
  hand-pinned. Hand-written Done/Still prose stays untouched; only the
  `<!-- derived:followup -->` fence carries the derived FollowupBlock.

  # ── Done-When checkbox parse (the done_pct source) ─────────────────────────

  Scenario: the Done-When checkbox ratio is parsed from the spec body
    Given a spec body with 4 of 7 Done-When boxes checked
    When I parse the Done-When section
    Then the checked/total is 4 of 7
    And done_pct equals checked over total

  Scenario: only the Done-When section's boxes are counted
    Given a spec body with boxes in Done-When and other boxes elsewhere
    When I parse the Done-When section
    Then only the Done-When boxes are counted

  # ── derivation invariants (rule 8) ─────────────────────────────────────────

  Scenario: a positive test count implies a test file in affects
    Given a FollowupBlock with test_count greater than zero
    Then at least one affects path is under tests/

  Scenario: status consistency is an audit, not a free pass
    Given a fully-checked spec marked shipped
    And a fully-checked spec marked draft
    Then the shipped one is status-consistent
    And the draft one is not status-consistent

  # ── determinism (re-run yields identical block) ────────────────────────────

  Scenario: rendering the derived block twice is identical
    Given a FollowupBlock derived from a fixture spec
    When I render it twice
    Then the two renders are identical

  # ── live tree ──────────────────────────────────────────────────────────────

  Scenario: recent commits derive from git log over affects paths
    Given the Spec 191 spec which has affects test files
    When I derive its FollowupBlock over the live tree
    Then recent_commits is a list of strings
    And done_when_total is at least 1
