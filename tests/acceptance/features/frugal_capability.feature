Feature: frugal capability — the ponytail port (Spec 348 Slice 1)
  The minimal-code discipline exposed as a discoverable, MCP-wired capability
  wrapping the core _frugal module (Spec 332 — single source for ladder + floor).

  Scenario: level reports the active discipline level (default full)
    When I read the frugal capability level
    Then the reported frugal level is "full"

  Scenario: set_level persists across a fresh read
    When I set the frugal capability level to "lite"
    And I read the frugal capability level
    Then the reported frugal level is "lite"

  Scenario: instructions returns the ruleset with the safety floor (the MCP port)
    When I get the frugal instructions at "ultra"
    Then the frugal instructions name every safety-floor marker
    And the reported frugal level is "ultra"

  Scenario: instructions at off are empty
    When I get the frugal instructions at "off"
    Then the frugal instructions are empty

  Scenario: help returns the complete reference card
    When I get the frugal help
    Then the frugal help contains "Levels (active:"
    And the frugal help contains "YAGNI"
