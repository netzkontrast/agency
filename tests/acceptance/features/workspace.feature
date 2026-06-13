Feature: Workspace capability — isolate and baseline
  workspace.isolate creates a git worktree and records a Workspace node;
  workspace.baseline runs a verification command and records the result
  with a BASELINED edge (Spec 002).

  Background:
    Given a fresh agency engine in code-mode
    And a confirmed intent

  Scenario: isolate records a Workspace node that SERVES the intent
    When I isolate branch "feature/safe-work"
    Then a Workspace node is recorded with the branch name
    And the Workspace SERVES the intent

  Scenario: baseline records a green result and BASELINED edge
    Given an isolated workspace for branch "feature/baseline"
    When I run the baseline command "pytest -q" in the workspace
    Then the baseline result reports passed true
    And the workspace has a BASELINED edge to the Baseline

  Scenario: baseline reports failure when the command fails
    Given an isolated workspace for branch "feature/failing"
    When I run a failing baseline command in the workspace
    Then the baseline result reports passed false

  Scenario: baseline returns an error for an unknown workspace id
    When I baseline against an unknown workspace id
    Then the baseline result carries an error
