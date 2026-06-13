Feature: Branch capability — commit_smart, assess, finish
  branch.commit_smart infers a conventional-commit message; branch.assess
  reads branch state and recommends an action; branch.finish records a
  BranchOutcome node (Spec 046).

  Background:
    Given a fresh agency engine in code-mode
    And a confirmed intent

  # ── commit_smart ─────────────────────────────────────────────────────────

  Scenario: commit_smart infers feat type for a new-feature summary
    When I call commit_smart with summary "add user profile page" and no paths
    Then the message starts with "feat"
    And the message contains "add user profile page"

  Scenario: commit_smart infers fix type from a fix-keyword summary
    When I call commit_smart with summary "fix broken login redirect" and no paths
    Then the message starts with "fix"

  Scenario: commit_smart infers test type when all paths are under tests/
    When I call commit_smart with summary "cover edge case" and paths "tests/test_foo.py,tests/test_bar.py"
    Then the message starts with "test"

  Scenario: commit_smart infers docs type when all paths are doc files
    When I call commit_smart with summary "update readme" and paths "docs/index.md"
    Then the message starts with "docs"

  Scenario: commit_smart infers scope from a capability path
    When I call commit_smart with summary "extend analyze" and paths "agency/capabilities/analyze/_main.py"
    Then the commit scope is "analyze"

  Scenario: commit_smart caps the subject at 60 characters
    When I call commit_smart with a very long summary
    Then the subject part of the message is at most 60 characters long

  # ── assess (stub VCS) ─────────────────────────────────────────────────────

  Scenario: assess recommends merge when branch is ahead and not behind
    Given a stub VCS that reports ahead 2 behind 0 dirty false
    When I call branch.assess for branch "feature/x" against base "main"
    Then the recommended action is "merge"

  Scenario: assess recommends pr when branch is behind
    Given a stub VCS that reports ahead 1 behind 3 dirty false
    When I call branch.assess for branch "feature/y" against base "main"
    Then the recommended action is "pr"

  Scenario: assess recommends keep when branch is dirty
    Given a stub VCS that reports ahead 1 behind 0 dirty true
    When I call branch.assess for branch "feature/z" against base "main"
    Then the recommended action is "keep"

  Scenario: assess recommends discard when branch has nothing ahead
    Given a stub VCS that reports ahead 0 behind 0 dirty false
    When I call branch.assess for branch "feature/empty" against base "main"
    Then the recommended action is "discard"

  # ── finish (stub VCS) ────────────────────────────────────────────────────

  Scenario: finish records a BranchOutcome node that SERVES the intent
    Given a stub VCS that succeeds for action "merge"
    When I call branch.finish with action "merge"
    Then a BranchOutcome node is recorded
    And the BranchOutcome SERVES the intent

  Scenario: finish returns an error for an unknown action
    When I call branch.finish with an unknown action
    Then the finish result carries an unknown-action error
