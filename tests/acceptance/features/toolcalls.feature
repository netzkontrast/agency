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
    When a Bash PostToolUse with an unknown command and 50-line output is captured
    Then the captured Bash row carries a shell-filtered view of the command
    And the full 50-line output is preserved in the row alongside the filtered view

  Scenario: pytest output keeps the failure summary, not the dot stream (Spec 337)
    Given a fresh engine
    When a Bash pytest PostToolUse with 200 dots then a failure summary is captured
    Then the pytest filtered view contains the failure summary
    And the pytest filtered view does not contain the dot progress stream
    And the full pytest output is retained verbatim in output_json

  Scenario: a Read tool call is captured as a locator, never as a body copy (Spec 337)
    Given a fresh engine
    When a Read PostToolUse for a 500-line file is captured
    Then the read filtered view contains the file path and line count
    And the read filtered view does not contain the file body
    And the full file body is retained verbatim in output_json

  Scenario: an unknown Bash command falls back to the Spec 336 head-20 view (Spec 337)
    Given a fresh engine
    When a Bash PostToolUse with an unknown command and 50-line output is captured
    Then the fallback filtered view is bounded to 20 lines
    And the full output is retained verbatim

  Scenario: a github MCP call is distilled to its decision fields (Spec 337)
    Given a fresh engine
    When a mcp__github__pull_request_read PostToolUse with a rich envelope is captured
    Then the github filtered view names the key decision fields
    And the github filtered view omits the envelope bulk
    And the full envelope is retained verbatim in output_json

  Scenario: per-tool filtered views are used in export top-calls (Spec 337)
    Given a fresh engine
    When a Read PostToolUse for a 500-line file is captured
    And I call toolcalls.export
    Then the export top list uses the locator view for the Read call

  Scenario: export distils the top calls into suggestions and a durable artefact (S4)
    Given an engine with several captured tool calls
    When I call toolcalls.export with apply
    Then the export ranks the repeated Bash call first in its top list
    And the export proposes a new-spec suggestion for the repeated command
    And a ToolcallExport artefact is recorded in the durable graph
