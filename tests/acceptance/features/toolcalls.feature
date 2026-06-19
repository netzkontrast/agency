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

  Scenario: a captured Bash call carries a shell-filtered view (S3)
    Given a fresh engine
    When a Bash PostToolUse with a 50-line output is captured
    Then the captured Bash row carries a shell-filtered view of the command
    And the full 50-line output is preserved in the row alongside the filtered view

  Scenario: export distils the top calls into suggestions and a durable artefact (S4)
    Given an engine with several captured tool calls
    When I call toolcalls.export with apply
    Then the export ranks the repeated Bash call first in its top list
    And the export proposes a new-spec suggestion for the repeated command
    And a ToolcallExport artefact is recorded in the durable graph
