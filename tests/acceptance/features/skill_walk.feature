Feature: Skill walk — atomic discipline execution (develop.skill_walk)
  skill_walk(name, inputs) runs a named discipline skill to the first hard gate
  and returns a documented status contract. On resumption the walk continues to
  completion. A paused walk is recorded in the graph as provenance.

  Background:
    Given a confirmed intent

  # ── core status-contract behaviours ─────────────────────────────────────────

  Scenario: walk pauses at the first hard gate
    When I walk the "tdd" skill with all phase inputs provided
    Then the status is "input-required"
    And the response names the blocked phase
    And the response carries a skill_id and partial_outputs

  Scenario: resuming a paused walk completes it
    When I walk the "tdd" skill with all phase inputs provided
    And I resume the walk with the same skill_id
    Then the status is "completed"
    And the skill_id is unchanged

  Scenario: unknown skill name returns the failed contract
    When I walk a skill named "no-such-skill" with no inputs
    Then the status is "failed"
    And the error mentions "no-such-skill"
    And the response lists available skills including "tdd"

  Scenario: missing required phase output aborts as failed
    When I walk the "tdd" skill with only the first phase input
    Then the status is "failed"
    And the response names the failing phase
    And the response lists the completed phases before the failure

  # ── provenance ───────────────────────────────────────────────────────────────

  Scenario: a walk records a Skill node serving the intent
    When I walk the "tdd" skill with all phase inputs provided
    Then a Skill node SERVES the intent in the graph

  Scenario: a paused walk records a BLOCKED_ON Gate in the graph
    When I walk the "tdd" skill with all phase inputs provided
    Then the Skill node has a BLOCKED_ON edge to a paused Gate

  # ── verb-bound phase execution ───────────────────────────────────────────────

  Scenario: a verb-bound phase executes its registered verb
    When I walk "authoring-capabilities" with scaffold inputs into a temp directory
    Then the scaffolded file is created on disk
    And the walk eventually reaches a failed or completed status

  # ── derived usage skills ─────────────────────────────────────────────────────

  Scenario: every verb-bearing capability has a walkable skill
    Given a fresh agency engine in code-mode
    Then every capability with verbs has at least one walkable skill

  Scenario: a derived usage skill has the correct shape
    Given a fresh agency engine in code-mode
    Then the "shell" capability has a derived usage skill
    And the usage skill ends with a hard gate
    And the usage skill references real verbs from the capability

  Scenario: walking a derived usage skill yields a valid status
    When I walk the derived skill "shell-usage" with no inputs
    Then the status is one of "completed", "input-required", "blocked", or "failed"

  Scenario: authored skills are not replaced by derived ones
    Given a fresh agency engine in code-mode
    Then the "develop" capability has its authored "tdd" skill
    And the "develop" capability does not have a "develop-usage" skill
