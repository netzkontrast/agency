Feature: The toolcalls capability — the clear MCP surface over tool-call capture (Spec 336 S2)
  Pre/post tool calls are captured in FULL into the ephemeral `.agency/toolcalls.db`,
  OFF the durable graph. This capability is the discoverable MCP surface over that
  store: inspect the stats, the top calls, and prune once distilled.

  Scenario: stats reports the capture broken down by phase and tool
    Given an engine with several captured tool calls
    When I call toolcalls.stats
    Then the stats total matches the captured count
    And the by-tool breakdown names Bash three times

  Scenario: top ranks the most-repeated call first
    Given an engine with several captured tool calls
    When I call toolcalls.top
    Then the top list ranks the most-repeated call first

  Scenario: prune clears the ephemeral store
    Given an engine with several captured tool calls
    When I call toolcalls.prune
    Then the store is emptied
